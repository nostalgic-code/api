import re
import logging
from collections import defaultdict
from typing import List, Dict, Any
import threading


class ProductSearchIndex:
    """
    Inverted index implementation for fast product searching
    
    This class builds and maintains an inverted index for product data,
    allowing for efficient keyword-based searches with improved scoring.
    """
    
    def __init__(self):
        """Initialize the search index"""
        self.index = defaultdict(set)  # word -> set of product_codes
        self.product_codes = set()  # all indexed product codes
        self.product_data = {}  # product_code -> product data for scoring
        self.is_initialized = False
        self._lock = threading.RLock()  # Thread safety
        self.logger = logging.getLogger(__name__)
    
    def build_index(self, products: List[Dict]) -> None:
        """
        Build the inverted index from a list of products
        
        Args:
            products: List of product dictionaries
        """
        with self._lock:
            self.index.clear()
            self.product_codes.clear()
            self.product_data.clear()
            
            for product in products:
                self._index_product(product)
            
            self.is_initialized = True
            self.logger.info(f"Index built with {len(products)} products")
    
    def _tokenize(self, text: Any) -> List[str]:
        """
        Convert text to lowercase tokens
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        if not text:
            return []
            
        # Convert to string if not already
        if not isinstance(text, str):
            text = str(text)
            
        # Normalize and split into words
        text = text.lower().strip()
        # Remove special characters and split, keeping alphanumeric
        words = re.findall(r'\w+', text)
        
        # Filter out very short tokens and common stop words
        stop_words = {'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        return [word for word in words if len(word) >= 2 and word not in stop_words]
    
    def _index_product(self, product: Dict) -> None:
        """
        Index a single product with field weighting
        
        Args:
            product: Product dictionary
        """
        product_code = product.get('product_code')
        if not product_code:
            return
            
        self.product_codes.add(product_code)
        self.product_data[product_code] = product
        
        # Index searchable fields with different weights
        field_weights = {
            'product_code': 3.0,  # Highest weight for exact code matches
            'brand': 2.0,
            'category': 1.5,
            'description': 1.0,
        }
        
        for field, weight in field_weights.items():
            if field in product and product[field]:
                tokens = self._tokenize(product[field])
                
                for token in tokens:
                    self.index[token].add(product_code)
        
        # Index part numbers with high weight
        if 'part_numbers' in product and product['part_numbers']:
            part_numbers = product['part_numbers']
            if isinstance(part_numbers, str):
                part_numbers = [part_numbers]
            
            for part_number in part_numbers:
                tokens = self._tokenize(part_number)
                for token in tokens:
                    self.index[token].add(product_code)
    
    def search(self, query: str, max_results: int = 100) -> List[str]:
        """
        Search the index for products matching the query with improved scoring
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of matching product codes, sorted by relevance
        """
        if not self.is_initialized:
            return []
            
        with self._lock:
            tokens = self._tokenize(query)
            if not tokens:
                return []
            
            # Calculate scores for each product
            scores = self._calculate_scores(tokens, query)
            
            if not scores:
                return []
            
            # Sort by score (descending) and return top results
            sorted_matches = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return [code for code, score in sorted_matches[:max_results]]
    
    def _calculate_scores(self, tokens: List[str], original_query: str) -> Dict[str, float]:
        """
        Calculate relevance scores for products based on token matches
        
        Args:
            tokens: List of search tokens
            original_query: Original search query
            
        Returns:
            Dictionary mapping product codes to scores
        """
        scores = defaultdict(float)
        
        for token in tokens:
            if token in self.index:
                matching_products = self.index[token]
                
                # Base score for token match
                token_score = 1.0
                
                # Boost for exact matches in product codes
                for product_code in matching_products:
                    score = token_score
                    
                    # Check for exact matches in different fields
                    product = self.product_data.get(product_code, {})
                    
                    # Boost for exact product code match
                    if product.get('product_code', '').lower() == token:
                        score *= 3.0
                    
                    # Boost for brand match
                    elif product.get('brand', '').lower() == token:
                        score *= 2.0
                    
                    # Boost for category match
                    elif product.get('category', '').lower() == token:
                        score *= 1.5
                    
                    scores[product_code] += score
        
        # Additional scoring for multi-token queries
        if len(tokens) > 1:
            self._apply_phrase_scoring(scores, tokens, original_query)
        
        return dict(scores)
    
    def _apply_phrase_scoring(self, scores: Dict[str, float], tokens: List[str], query: str) -> None:
        """
        Apply additional scoring for phrase matches
        
        Args:
            scores: Current scores dictionary
            tokens: List of search tokens
            query: Original query string
        """
        query_lower = query.lower()
        
        for product_code in list(scores.keys()):
            product = self.product_data.get(product_code, {})
            
            # Check for phrase matches in description
            description = product.get('description', '').lower()
            if query_lower in description:
                scores[product_code] *= 1.5
            
            # Boost for having all tokens
            token_matches = sum(1 for token in tokens if token in description)
            if token_matches == len(tokens):
                scores[product_code] *= 1.2
    
    def add_product(self, product: Dict) -> None:
        """
        Add a new product to the index
        
        Args:
            product: Product dictionary
        """
        with self._lock:
            self._index_product(product)
    
    def remove_product(self, product_code: str) -> None:
        """
        Remove a product from the index
        
        Args:
            product_code: Product code to remove
        """
        with self._lock:
            if product_code in self.product_codes:
                self.product_codes.remove(product_code)
                self.product_data.pop(product_code, None)
                
                # Remove from all token entries and clean up empty entries
                empty_tokens = []
                for token, codes in self.index.items():
                    if product_code in codes:
                        codes.remove(product_code)
                        if not codes:  # Mark empty entries for cleanup
                            empty_tokens.append(token)
                
                # Clean up empty token entries
                for token in empty_tokens:
                    del self.index[token]
    
    def update_product(self, product: Dict) -> None:
        """
        Update a product in the index
        
        Args:
            product: Updated product dictionary
        """
        product_code = product.get('product_code')
        if not product_code:
            return
            
        with self._lock:
            # Remove old entries
            self.remove_product(product_code)
            
            # Add updated product
            self._index_product(product)
    
    def get_suggestions(self, partial_query: str, max_suggestions: int = 5) -> List[str]:
        """
        Get search suggestions for partial queries
        
        Args:
            partial_query: Partial search string
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested search terms
        """
        if not partial_query or len(partial_query) < 2:
            return []
            
        partial_lower = partial_query.lower()
        suggestions = set()
        
        with self._lock:
            for token in self.index.keys():
                if token.startswith(partial_lower):
                    suggestions.add(token)
                    if len(suggestions) >= max_suggestions:
                        break
        
        return sorted(list(suggestions))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics
        
        Returns:
            Dictionary with index statistics
        """
        with self._lock:
            return {
                'total_products': len(self.product_codes),
                'total_tokens': len(self.index),
                'is_initialized': self.is_initialized,
                'average_tokens_per_product': len(self.index) / max(len(self.product_codes), 1)
            }