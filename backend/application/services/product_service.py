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
    products = service.get_products_by_category('electronics')

Author: Development Team
Version: 1.0
"""

# TODO: Implement ProductService class with methods for:
# - get_products(filters=None, pagination=None)
# - get_product_by_code(product_code)
# - search_products(query, filters=None)
# - get_products_by_category(category)
# - get_products_by_brand(brand)
# - get_product_statistics()
# - validate_product_data(product_data)



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
    products = service.get_products_by_category('electronics')

Author: Development Team
Version: 1.0
"""

from flask import jsonify
from typing import Dict, List, Optional, Any, Tuple
import logging
import re
from decimal import Decimal, InvalidOperation
import ProductSearchIndex

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
            from backend.application.utils.database import DatabaseConnection
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
        
        Args:
            filters: Dictionary of filter criteria
            pagination: Dictionary with page, limit parameters
            
        Returns:
            Dictionary containing products and metadata
        """
        try:
            db = self._get_db_connection()
            
            # Default pagination
            if pagination is None:
                pagination = {"page": 1, "limit": 20}
            
            page = pagination.get("page", 1)
            limit = pagination.get("limit", 20)
            
            # Build query conditions
            where_conditions = []
            params = []
            
            if filters:
                if filters.get("available_only", True):
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
                
                if filters.get("search"):
                    where_conditions.append("(description LIKE %s OR brand LIKE %s OR product_code LIKE %s)")
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term, search_term])
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
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
                ORDER BY brand, description
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
                    "items_per_page": limit
                },
                "filters_applied": filters or {}
            }
            
            db.disconnect()
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting products: {str(e)}")
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
            
            db = self._get_db_connection()
            
            query = """
                SELECT product_code, description, category, brand, current_price, 
                       quantity_available, unit_of_measure, part_numbers, is_available
                FROM products 
                WHERE product_code = %s
            """
            
            result = db.execute_query(query, [product_code.strip()])
            
            if not result:
                db.disconnect()
                return None
            
            product = self._format_product(result[0])
            db.disconnect()
            return product
            
        except Exception as e:
            self.logger.error(f"Error getting product by code {product_code}: {str(e)}")
            raise
    
    def search_products(self, query: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Search products by query string
        
        Args:
            query: Search query string
            filters: Additional filter criteria
            
        Returns:
            Dictionary containing matching products
        """
        try:
            if not query or not query.strip():
                raise ValueError("Search query is required")
            
            # Use inverted index for initial search
            matching_codes = self.search_index.search(query.strip())

            if not matching_codes:
                return {
                    "products": [],
                    "count": 0,
                    "query": query,
                    "filters_applied": filters or {}
                }
            
            db = self._get_db_connection()







            # Build filter conditions
            where_conditions = [f"product_code IN ({', '.join(['%s'] * len(matching_codes))})"]
            params = matching_codes.copy()
            
            if filters:
                if filters.get("available_only", True):
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
            
            where_clause = " AND ".join(where_conditions)
            
            # Get filtered products
            query = f"""
                SELECT product_code, description, category, brand, current_price, 
                       quantity_available, unit_of_measure, part_numbers, is_available
                FROM products 
                WHERE {where_clause}
            """
            
            results = db.execute_query(query, params)
            products = [self._format_product(row) for row in results]
            
            # Maintain the order from the search index (relevance order)
            ordered_products = []
            product_map = {p["product_code"]: p for p in products}
            
            for code in matching_codes:
                if code in product_map:
                    ordered_products.append(product_map[code])
            
            db.disconnect()
            return {
                "products": ordered_products,
                "count": len(ordered_products),
                "query": query,
                "filters_applied": filters or {}
            }
            
        except Exception as e:
            self.logger.error(f"Error searching products: {str(e)}")
            raise














            
        #     # Build search conditions
        #     where_conditions = []
        #     params = []
            
        #     # Main search condition
        #     search_term = f"%{query.strip()}%"
        #     where_conditions.append("""
        #         (description LIKE %s OR brand LIKE %s OR product_code LIKE %s 
        #          OR category LIKE %s OR part_numbers LIKE %s)
        #     """)
        #     params.extend([search_term] * 5)
            
        #     # Apply additional filters
        #     if filters:
        #         if filters.get("available_only", True):
        #             where_conditions.append("is_available = TRUE")
                
        #         if filters.get("category"):
        #             where_conditions.append("category = %s")
        #             params.append(filters["category"])
                
        #         if filters.get("brand"):
        #             where_conditions.append("brand = %s")
        #             params.append(filters["brand"])
                
        #         if filters.get("min_price") is not None:
        #             where_conditions.append("current_price >= %s")
        #             params.append(filters["min_price"])
                
        #         if filters.get("max_price") is not None:
        #             where_conditions.append("current_price <= %s")
        #             params.append(filters["max_price"])
            
        #     where_clause = " AND ".join(where_conditions)
            
        #     # Execute search
        #     search_query = f"""
        #         SELECT product_code, description, category, brand, current_price, 
        #                quantity_available, unit_of_measure, part_numbers, is_available
        #         FROM products 
        #         WHERE {where_clause}
        #         ORDER BY 
        #             CASE WHEN product_code LIKE %s THEN 1 ELSE 2 END,
        #             CASE WHEN description LIKE %s THEN 1 ELSE 2 END,
        #             brand, description
        #         LIMIT 10
        #     """
        #     # Add relevance sorting parameters
        #     params.extend([f"%{query.strip()}%", f"%{query.strip()}%"])
            
        #     results = db.execute_query(search_query, params)
            
        #     products = [self._format_product(row) for row in results]
            
        #     db.disconnect()
        #     return {
        #         "products": products,
        #         "count": len(products),
        #         "query": query,
        #         "filters_applied": filters or {}
        #     }
            
        # except Exception as e:
        #     self.logger.error(f"Error searching products: {str(e)}")
        #     raise

    def search_products_by_codes():
        """Search products by multiple product codes or partial product code match (Flask endpoint function)"""
        try:
            from flask import request
            
            # Get query parameters
            product_codes = request.args.get('codes')  # Comma-separated list
            partial_code = request.args.get('partial')  # Partial code search
            exact = request.args.get('exact', 'false').lower() == 'true'  # Exact match flag
            
            if not product_codes and not partial_code:
                return jsonify({"error": "Either 'codes' or 'partial' parameter is required"}), 400
            
            service = ProductService()
            
            if product_codes:
                # Handle multiple specific product codes
                code_list = [code.strip() for code in product_codes.split(',')]
                products = []
                for code in code_list:
                    product = service.get_product_by_code(code)
                    if product:
                        products.append(product)
                
                return jsonify({
                    "products": products,
                    "count": len(products)
                }), 200
            
            elif partial_code:
                # Handle partial search
                if exact:
                    # Exact match
                    product = service.get_product_by_code(partial_code)
                    products = [product] if product else []
                else:
                    # Partial match using search
                    result = service.search_products(partial_code)
                    products = result["products"]
                
                return jsonify({
                    "products": products,
                    "count": len(products)
                }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get products by category
        
        Args:
            category: Product category
            
        Returns:
            List of products in the category
        """
        try:
            if not category or not category.strip():
                raise ValueError("Category is required")
            
            db = self._get_db_connection()
            
            query = """
                SELECT product_code, description, category, brand, current_price, 
                       quantity_available, unit_of_measure, part_numbers, is_available
                FROM products 
                WHERE category = %s AND is_available = TRUE
                ORDER BY brand, description
            """
            
            results = db.execute_query(query, [category.strip()])
            products = [self._format_product(row) for row in results]
            
            db.disconnect()
            return products
            
        except Exception as e:
            self.logger.error(f"Error getting products by category {category}: {str(e)}")
            raise
    
    def get_products_by_brand(self, brand: str) -> List[Dict[str, Any]]:
        """
        Get products by brand
        
        Args:
            brand: Product brand
            
        Returns:
            List of products from the brand
        """
        try:
            if not brand or not brand.strip():
                raise ValueError("Brand is required")
            
            db = self._get_db_connection()
            
            query = """
                SELECT product_code, description, category, brand, current_price, 
                       quantity_available, unit_of_measure, part_numbers, is_available
                FROM products 
                WHERE brand = %s AND is_available = TRUE
                ORDER BY category, description
            """
            
            results = db.execute_query(query, [brand.strip()])
            products = [self._format_product(row) for row in results]
            
            db.disconnect()
            return products
            
        except Exception as e:
            self.logger.error(f"Error getting products by brand {brand}: {str(e)}")
            raise
    
    def get_product_statistics(self) -> Dict[str, Any]:
        """
        Get product statistics and metrics
        
        Returns:
            Dictionary containing various product statistics
        """
        try:
            db = self._get_db_connection()
            
            # Total products
            total_query = "SELECT COUNT(*) FROM products"
            total_result = db.execute_query(total_query)
            total_products = total_result[0][0] if total_result else 0
            
            # Available products
            available_query = "SELECT COUNT(*) FROM products WHERE is_available = TRUE"
            available_result = db.execute_query(available_query)
            available_products = available_result[0][0] if available_result else 0
            
            # Products by category
            category_query = """
                SELECT category, COUNT(*) as count 
                FROM products 
                WHERE is_available = TRUE 
                GROUP BY category 
                ORDER BY count DESC
            """
            category_results = db.execute_query(category_query)
            categories = [{"category": row[0], "count": row[1]} for row in category_results]
            
            # Products by brand
            brand_query = """
                SELECT brand, COUNT(*) as count 
                FROM products 
                WHERE is_available = TRUE 
                GROUP BY brand 
                ORDER BY count DESC 
                LIMIT 10
            """
            brand_results = db.execute_query(brand_query)
            top_brands = [{"brand": row[0], "count": row[1]} for row in brand_results]
            
            # Price statistics
            price_query = """
                SELECT 
                    MIN(current_price) as min_price,
                    MAX(current_price) as max_price,
                    AVG(current_price) as avg_price,
                    COUNT(CASE WHEN current_price < 100 THEN 1 END) as under_100,
                    COUNT(CASE WHEN current_price BETWEEN 100 AND 500 THEN 1 END) as between_100_500,
                    COUNT(CASE WHEN current_price > 500 THEN 1 END) as over_500
                FROM products 
                WHERE is_available = TRUE AND current_price > 0
            """
            price_result = db.execute_query(price_query)
            
            price_stats = {}
            if price_result and price_result[0][0] is not None:
                row = price_result[0]
                price_stats = {
                    "min_price": float(row[0]),
                    "max_price": float(row[1]),
                    "avg_price": round(float(row[2]), 2),
                    "price_ranges": {
                        "under_100": row[3],
                        "between_100_500": row[4],
                        "over_500": row[5]
                    }
                }
            
            statistics = {
                "total_products": total_products,
                "available_products": available_products,
                "unavailable_products": total_products - available_products,
                "categories": categories,
                "top_brands": top_brands,
                "price_statistics": price_stats
            }
            
            db.disconnect()
            return statistics
            
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
            
            # Category and brand validation
            for field in ["category", "brand"]:
                if product_data.get(field):
                    value = product_data[field].strip()
                    if len(value) > 100:
                        errors.append(f"{field.capitalize()} cannot exceed 100 characters")
            
            # Unit of measure validation
            if product_data.get("unit_of_measure"):
                uom = product_data["unit_of_measure"].strip()
                if len(uom) > 20:
                    errors.append("Unit of measure cannot exceed 20 characters")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"Error validating product data: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    def get_categories(self) -> List[str]:
        """Get all available product categories"""
        try:
            db = self._get_db_connection()
            
            query = """
                SELECT DISTINCT category 
                FROM products 
                WHERE category IS NOT NULL AND category != ''
                ORDER BY category
            """
            
            results = db.execute_query(query)
            categories = [row[0] for row in results if row[0]]
            
            db.disconnect()
            return categories
            
        except Exception as e:
            self.logger.error(f"Error getting categories: {str(e)}")
            raise
    
    def get_brands(self) -> List[str]:
        """Get all available product brands"""
        try:
            db = self._get_db_connection()
            
            query = """
                SELECT DISTINCT brand 
                FROM products 
                WHERE brand IS NOT NULL AND brand != ''
                ORDER BY brand
            """
            
            results = db.execute_query(query)
            brands = [row[0] for row in results if row[0]]
            
            db.disconnect()
            return brands
            
        except Exception as e:
            self.logger.error(f"Error getting brands: {str(e)}")
            raise


    # NotImplemented
    # def _format_product(self, row) -> Dict:
    #     """Format database row into product dictionary"""
    #     # Implementation depends on your database structure
    #     # This is a placeholder
    #     return {
    #         'product_code': row[0],
    #         'description': row[1],
    #         'category': row[2],
    #         'brand': row[3],
    #         'current_price': row[4],
    #         'quantity_available': row[5],
    #         'unit_of_measure': row[6],
    #         'part_numbers': row[7],
    #         'is_available': row[8]
    #     }