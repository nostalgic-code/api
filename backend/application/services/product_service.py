"""
Product Service Module

This module provides business logic and data access layer for product operations.
It handles product CRUD operations, search functionality, and business rules
for the marketplace application.

Key Features:
- Product data retrieval and management
- Search and filtering capabilities
- Business logic for product operations
- Data validation and transformation
- Integration with database layer

Classes:
    ProductService: Main service class for product operations

Dependencies:
    - Database connection utilities
    - Product model classes
    - Validation utilities

Usage:
    service = ProductService()
    products = service.get_products(filters={'category': 'electronics'})

Author: Development Team
Version: 2.0
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime

from application.services.product_search_index import ProductSearchIndex


class ProductService:
    """
    Main service class for product operations
    
    Provides business logic layer for product management, including
    data retrieval, validation, and transformation operations.
    """
    
    def __init__(self):
        """Initialize the ProductService"""
        self.logger = logging.getLogger(__name__)
        self.search_index = ProductSearchIndex()
        self._initialize_search_index()
    
    def _get_db_connection(self):
        """Get database connection with error handling"""
        try:
            from application.utils.database import DatabaseConnection
            db = DatabaseConnection()
            if not db.connect():
                raise Exception("Database connection failed")
            return db
        except ImportError:
            raise Exception("Database utilities not available")
    
    def _initialize_search_index(self):
        """Initialize the search index with all products"""
        try:
            db = self._get_db_connection()
            
            query = """
                SELECT product_code, description, category, brand, current_price, 
                       quantity_available, unit_of_measure, part_numbers, is_available
                FROM products
            """
            
            results = db.execute_query(query)
            products = [self._format_product(row) for row in results]
            self.search_index.build_index(products)
            
            db.disconnect()
            self.logger.info(f"Search index initialized with {len(products)} products")
            
        except Exception as e:
            self.logger.error(f"Error initializing search index: {str(e)}")

    def _format_product(self, row: Tuple) -> Dict[str, Any]:
        """Format database row into product dictionary"""
        return {
            "product_code": row[0],
            "description": row[1],
            "category": row[2],
            "brand": row[3],
            "price": float(row[4]) if row[4] is not None else 0.0,
            "quantity_available": row[5] if row[5] is not None else 0,
            "unit_of_measure": row[6],
            "part_numbers": row[7] if row[7] else [],
            "is_available": row[8] if len(row) > 8 else True
        }
    
    def get_products(self, filters: Optional[Dict] = None, pagination: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get products with optional filters and pagination
        
        This is the main method for retrieving products. It supports:
        - Pagination
        - Filtering by category, brand, price range, availability
        - Simple text search (for non-indexed search)
        - Sorting options
        
        Args:
            filters: Dictionary of filter criteria
                - category: str
                - brand: str
                - min_price: float
                - max_price: float
                - available_only: bool (default True)
                - search: str (simple text search)
                - product_codes: List[str] (specific product codes)
                - sort_by: str (price_asc, price_desc, name_asc, name_desc)
            pagination: Dictionary with page, limit parameters
            
        Returns:
            Dictionary containing products and metadata
        """
        try:
            db = self._get_db_connection()
            
            # Default pagination
            if pagination is None:
                pagination = {"page": 1, "limit": 20}
            
            page = max(1, pagination.get("page", 1))
            limit = min(100, pagination.get("limit", 20))  # Cap at 100 for performance
            
            # Build query conditions
            where_conditions = []
            params = []
            
            if filters:
                if filters.get("available_only", False):
                    where_conditions.append("is_available = TRUE")
                
                if filters.get("category"):
                    where_conditions.append("category = %s")
                    params.append(filters["category"])
                
                if filters.get("brand"):
                    where_conditions.append("brand = %s")
                    params.append(filters["brand"])
                
                if filters.get("min_price") is not None:
                    where_conditions.append("current_price >= %s")
                    params.append(filters["min_price"])
                
                if filters.get("max_price") is not None:
                    where_conditions.append("current_price <= %s")
                    params.append(filters["max_price"])
                
                # Handle specific product codes
                if filters.get("product_codes"):
                    codes = filters["product_codes"]
                    if isinstance(codes, str):
                        codes = [codes]
                    placeholders = ', '.join(['%s'] * len(codes))
                    where_conditions.append(f"product_code IN ({placeholders})")
                    params.extend(codes)
                
                # Simple text search (fallback when not using search endpoint)
                if filters.get("search"):
                    where_conditions.append("(description LIKE %s OR brand LIKE %s OR product_code LIKE %s)")
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term, search_term])
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Determine sort order
            sort_clause = "ORDER BY brand, description"  # Default
            if filters and filters.get("sort_by"):
                sort_map = {
                    "price_asc": "current_price ASC",
                    "price_desc": "current_price DESC",
                    "name_asc": "description ASC",
                    "name_desc": "description DESC",
                    "newest": "created_at DESC",  # If you have created_at column
                }
                sort_clause = f"ORDER BY {sort_map.get(filters['sort_by'], 'brand, description')}"
            
            # Count total
            count_query = f"SELECT COUNT(*) FROM products WHERE {where_clause}"
            total_result = db.execute_query(count_query, params)
            total = total_result[0][0] if total_result else 0
            
            # Get products
            offset = (page - 1) * limit
            query = f"""
                SELECT product_code, description, category, brand, current_price, 
                       quantity_available, unit_of_measure, part_numbers, is_available
                FROM products 
                WHERE {where_clause}
                {sort_clause}
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            
            products = db.execute_query(query, params)
            
            result = {
                "products": [self._format_product(row) for row in products],
                "pagination": {
                    "current_page": page,
                    "total_pages": (total + limit - 1) // limit,
                    "total_items": total,
                    "items_per_page": limit,
                    "has_next": page < (total + limit - 1) // limit,
                    "has_previous": page > 1
                },
                "filters_applied": filters or {}
            }
            
            db.disconnect()
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting products: {str(e)}")
            raise
    
    def search_products(self, query: str, filters: Optional[Dict] = None, pagination: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Search products using the inverted index for fast, relevant results
        
        Args:
            query: Search query string
            filters: Additional filter criteria (same as get_products)
            pagination: Dictionary with page, limit parameters
            
        Returns:
            Dictionary containing matching products ordered by relevance
        """
        try:
            if not query or not query.strip():
                # If no query, fall back to regular product listing
                return self.get_products(filters, pagination)
            
            # Use inverted index for initial search
            matching_codes = self.search_index.search(query.strip(), max_results=500)

            if not matching_codes:
                return {
                    "products": [],
                    "pagination": {
                        "current_page": 1,
                        "total_pages": 0,
                        "total_items": 0,
                        "items_per_page": pagination.get("limit", 20) if pagination else 20,
                        "has_next": False,
                        "has_previous": False
                    },
                    "query": query,
                    "filters_applied": filters or {}
                }
            
            # Apply filters with the matching codes
            if not filters:
                filters = {}
            filters["product_codes"] = matching_codes
            
            # Get filtered products
            result = self.get_products(filters, pagination)
            
            # Maintain relevance order from search index
            if result["products"]:
                product_map = {p["product_code"]: p for p in result["products"]}
                ordered_products = []
                
                for code in matching_codes:
                    if code in product_map:
                        ordered_products.append(product_map[code])
                
                result["products"] = ordered_products[:len(result["products"])]
            
            # Add search-specific metadata
            result["query"] = query
            result["search_suggestions"] = self.search_index.get_suggestions(query, max_suggestions=5)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error searching products: {str(e)}")
            raise
    
    def get_product_by_code(self, product_code: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific product by product code
        
        Args:
            product_code: The product code to search for
            
        Returns:
            Product dictionary or None if not found
        """
        try:
            if not product_code or not product_code.strip():
                raise ValueError("Product code is required")
            
            result = self.get_products(filters={"product_codes": [product_code.strip()]})
            
            if result["products"]:
                return result["products"][0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting product by code {product_code}: {str(e)}")
            raise
    
    def get_related_products(self, product_code: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get related/alternative products for cross-selling
        
        Args:
            product_code: Base product code
            limit: Maximum number of related products
            
        Returns:
            List of related products
        """
        try:
            # Get the base product
            base_product = self.get_product_by_code(product_code)
            if not base_product:
                return []
            
            # Find products in same category and brand
            filters = {
                "category": base_product["category"],
                "available_only": True
            }
            
            result = self.get_products(filters, {"limit": limit + 1})
            
            # Remove the base product and return
            related = [p for p in result["products"] if p["product_code"] != product_code]
            
            return related[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting related products for {product_code}: {str(e)}")
            return []
    
    def get_product_statistics(self) -> Dict[str, Any]:
        """
        Get product statistics and metrics for admin dashboard
        
        Returns:
            Dictionary containing various product statistics
        """
        try:
            db = self._get_db_connection()
            
            stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {},
                "by_category": [],
                "by_brand": [],
                "price_distribution": {},
                "stock_alerts": []
            }
            
            # Summary statistics
            summary_query = """
                SELECT 
                    COUNT(*) as total_products,
                    COUNT(CASE WHEN is_available = TRUE THEN 1 END) as available_products,
                    COUNT(CASE WHEN quantity_available = 0 THEN 1 END) as out_of_stock,
                    COUNT(CASE WHEN quantity_available < 10 AND quantity_available > 0 THEN 1 END) as low_stock
                FROM products
            """
            
            result = db.execute_query(summary_query)
            if result:
                row = result[0]
                stats["summary"] = {
                    "total_products": row[0],
                    "available_products": row[1],
                    "out_of_stock": row[2],
                    "low_stock": row[3]
                }
            
            # Products by category
            category_query = """
                SELECT category, COUNT(*) as count, AVG(current_price) as avg_price
                FROM products 
                WHERE is_available = TRUE 
                GROUP BY category 
                ORDER BY count DESC
            """
            category_results = db.execute_query(category_query)
            stats["by_category"] = [
                {
                    "category": row[0], 
                    "count": row[1],
                    "average_price": round(float(row[2]), 2) if row[2] else 0
                } 
                for row in category_results
            ]
            
            # Top brands
            brand_query = """
                SELECT brand, COUNT(*) as count 
                FROM products 
                WHERE is_available = TRUE 
                GROUP BY brand 
                ORDER BY count DESC 
                LIMIT 10
            """
            brand_results = db.execute_query(brand_query)
            stats["by_brand"] = [
                {"brand": row[0], "count": row[1]} 
                for row in brand_results
            ]
            
            # Price distribution - MySQL compatible version
            price_query = """
                SELECT 
                    MIN(current_price) as min_price,
                    MAX(current_price) as max_price,
                    AVG(current_price) as avg_price
                FROM products 
                WHERE is_available = TRUE AND current_price > 0
            """
            price_result = db.execute_query(price_query)
            
            if price_result and price_result[0][0] is not None:
                row = price_result[0]
                stats["price_distribution"] = {
                    "min": float(row[0]),
                    "max": float(row[1]),
                    "average": round(float(row[2]), 2)
                }
                
                # Calculate median separately for MySQL
                median_query = """
                    SELECT current_price
                    FROM (
                        SELECT current_price, @rownum:=@rownum+1 as row_number, @total_rows:=@rownum
                        FROM products, (SELECT @rownum:=0) r
                        WHERE is_available = TRUE AND current_price > 0
                        ORDER BY current_price
                    ) as t
                    WHERE row_number IN (FLOOR((@total_rows+1)/2), FLOOR((@total_rows+2)/2))
                """
                
                # Alternative simpler approach for median
                count_query = "SELECT COUNT(*) FROM products WHERE is_available = TRUE AND current_price > 0"
                count_result = db.execute_query(count_query)
                total_count = count_result[0][0] if count_result else 0
                
                if total_count > 0:
                    # For MySQL, we'll use a simpler approach to get approximate median
                    limit = 1
                    offset = total_count // 2
                    median_simple_query = """
                        SELECT current_price 
                        FROM products 
                        WHERE is_available = TRUE AND current_price > 0
                        ORDER BY current_price
                        LIMIT %s OFFSET %s
                    """
                    median_result = db.execute_query(median_simple_query, [limit, offset])
                    if median_result:
                        stats["price_distribution"]["median"] = float(median_result[0][0])
                    else:
                        stats["price_distribution"]["median"] = stats["price_distribution"]["average"]
                else:
                    stats["price_distribution"]["median"] = 0
            
            # Get low stock alerts
            low_stock_query = """
                SELECT product_code, description, quantity_available
                FROM products
                WHERE is_available = TRUE 
                AND quantity_available > 0 
                AND quantity_available < 10
                ORDER BY quantity_available ASC
                LIMIT 20
            """
            low_stock_results = db.execute_query(low_stock_query)
            stats["stock_alerts"] = [
                {
                    "product_code": row[0],
                    "description": row[1],
                    "quantity_available": row[2]
                }
                for row in low_stock_results
            ]
            
            db.disconnect()
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting product statistics: {str(e)}")
            raise
    
    def validate_product_data(self, product_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate product data
        
        Args:
            product_data: Dictionary containing product information
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Required fields
            required_fields = ["product_code", "description", "category", "brand", "current_price"]
            
            for field in required_fields:
                if not product_data.get(field):
                    errors.append(f"Field '{field}' is required")
                elif isinstance(product_data[field], str) and not product_data[field].strip():
                    errors.append(f"Field '{field}' cannot be empty")
            
            # Product code validation
            if product_data.get("product_code"):
                product_code = product_data["product_code"].strip()
                if len(product_code) < 3:
                    errors.append("Product code must be at least 3 characters long")
                if not re.match(r'^[A-Za-z0-9\-_]+$', product_code):
                    errors.append("Product code can only contain letters, numbers, hyphens, and underscores")
            
            # Price validation
            if product_data.get("current_price") is not None:
                try:
                    price = Decimal(str(product_data["current_price"]))
                    if price < 0:
                        errors.append("Price cannot be negative")
                    if price > Decimal("999999.99"):
                        errors.append("Price cannot exceed 999,999.99")
                except (InvalidOperation, ValueError):
                    errors.append("Price must be a valid number")
            
            # Quantity validation
            if product_data.get("quantity_available") is not None:
                try:
                    quantity = int(product_data["quantity_available"])
                    if quantity < 0:
                        errors.append("Quantity cannot be negative")
                    if quantity > 999999:
                        errors.append("Quantity cannot exceed 999,999")
                except (ValueError, TypeError):
                    errors.append("Quantity must be a valid integer")
            
            # Description validation
            if product_data.get("description"):
                description = product_data["description"].strip()
                if len(description) < 10:
                    errors.append("Description must be at least 10 characters long")
                if len(description) > 1000:
                    errors.append("Description cannot exceed 1000 characters")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"Error validating product data: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    def get_filter_options(self) -> Dict[str, List[Any]]:
        """
        Get available filter options for the product catalog
        
        Returns:
            Dictionary with available categories, brands, and price ranges
        """
        try:
            db = self._get_db_connection()
            
            # Get categories
            category_query = """
                SELECT DISTINCT category 
                FROM products 
                WHERE category IS NOT NULL AND category != '' AND is_available = TRUE
                ORDER BY category
            """
            categories = [row[0] for row in db.execute_query(category_query)]
            
            # Get brands
            brand_query = """
                SELECT DISTINCT brand 
                FROM products 
                WHERE brand IS NOT NULL AND brand != '' AND is_available = TRUE
                ORDER BY brand
            """
            brands = [row[0] for row in db.execute_query(brand_query)]
            
            # Get price range
            price_query = """
                SELECT MIN(current_price), MAX(current_price)
                FROM products
                WHERE is_available = TRUE AND current_price > 0
            """
            price_result = db.execute_query(price_query)
            
            price_range = {
                "min": float(price_result[0][0]) if price_result and price_result[0][0] else 0,
                "max": float(price_result[0][1]) if price_result and price_result[0][1] else 0
            }
            
            db.disconnect()
            
            return {
                "categories": categories,
                "brands": brands,
                "price_range": price_range,
                "sort_options": [
                    {"value": "relevance", "label": "Relevance"},
                    {"value": "price_asc", "label": "Price: Low to High"},
                    {"value": "price_desc", "label": "Price: High to Low"},
                    {"value": "name_asc", "label": "Name: A to Z"},
                    {"value": "name_desc", "label": "Name: Z to A"}
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting filter options: {str(e)}")
            raise