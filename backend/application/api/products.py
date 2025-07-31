"""
Products API Module

This module provides RESTful API endpoints for product operations in the
marketplace application. It handles product retrieval, search, filtering,
and provides JSON responses for frontend consumption.

Key Features:
- RESTful product endpoints
- Advanced search and filtering
- Pagination support
- Category and brand filtering
- Price range queries
- Product availability checks
- JSON response formatting

Endpoints:
    GET /products - List products with optional filters
    GET /products/filters - Get available filter options
    GET /products/search - Search products by query
    GET /products/statistics - Get product statistics (admin only)
    GET /products/<product_code> - Get specific product details
    GET /products/<product_code>/related - Get related products

Dependencies:
    - Flask Blueprint for route organization
    - Product service layer for business logic
    - Database utilities for data access
    - Validation utilities for input validation

Usage:
    from app.api.products import products_bp
    app.register_blueprint(products_bp)

Author: Development Team
Version: 2.0
"""

from flask import Blueprint, request, jsonify, g
from application.services.product_service import ProductService
from application.middleware.auth import (
    token_required, 
    permission_required, 
    platform_user_required,
    customer_user_required
)

products_bp = Blueprint('products', __name__)
service = ProductService()


def parse_pagination():
    """Parse pagination parameters from request"""
    return {
        "page": request.args.get('page', default=1, type=int),
        "limit": request.args.get('limit', default=20, type=int)
    }


def parse_filters():
    """Parse common filter parameters from request"""
    filters = {
        "available_only": request.args.get('available_only', 'true').lower() == 'true',
        "category": request.args.get('category'),
        "brand": request.args.get('brand'),
        "min_price": request.args.get('min_price', type=float),
        "max_price": request.args.get('max_price', type=float),
        "sort_by": request.args.get('sort_by')
    }
    # Remove None values
    return {k: v for k, v in filters.items() if v is not None}


@products_bp.route('/', methods=['GET'])
@token_required
@permission_required('products', 'read')
def get_products():
    """
    Get paginated list of products with optional filtering
    
    Query Parameters:
        - page (int): Page number (default: 1)
        - limit (int): Items per page (default: 20, max: 100)
        - available_only (bool): Show only available products (default: true)
        - category (str): Filter by category
        - brand (str): Filter by brand
        - min_price (float): Minimum price filter
        - max_price (float): Maximum price filter
        - sort_by (str): Sort order (price_asc, price_desc, name_asc, name_desc)
        - search (str): Simple text search (searches in description, brand, product_code)
    
    Returns:
        JSON response with products array and pagination metadata
    """
    try:
        filters = parse_filters()
        
        # Add search parameter if present
        search = request.args.get('search')
        if search:
            filters['search'] = search
            
        pagination = parse_pagination()
        
        result = service.get_products(filters=filters, pagination=pagination)
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@products_bp.route('/search', methods=['GET'])
@token_required
@permission_required('products', 'read')
def search_products():
    """
    Search products using fast indexed search
    
    Query Parameters:
        - q, query, or search (str): Search query (required)
        - page (int): Page number (default: 1)
        - limit (int): Items per page (default: 20, max: 100)
        - available_only (bool): Show only available products (default: true)
        - category (str): Filter by category
        - brand (str): Filter by brand
        - min_price (float): Minimum price filter
        - max_price (float): Maximum price filter
        - sort_by (str): Sort order (relevance is default for search)
    
    Returns:
        JSON response with products array, pagination metadata, and search suggestions
    """
    try:
        # Get search query from various possible parameter names
        query = request.args.get('q') or request.args.get('query') or request.args.get('search')
        if not query:
            return jsonify({
                "error": "Search query parameter 'q', 'query', or 'search' is required"
            }), 400
        
        filters = parse_filters()
        pagination = parse_pagination()
        
        result = service.search_products(query, filters=filters, pagination=pagination)
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@products_bp.route('/filters', methods=['GET'])
@token_required
@permission_required('products', 'read')
def get_filter_options():
    """
    Get available filter options for the product catalog
    
    Returns:
        JSON response with:
        - categories: List of available categories
        - brands: List of available brands
        - price_range: Min and max prices
        - sort_options: Available sorting options
    """
    try:
        filter_options = service.get_filter_options()
        return jsonify(filter_options), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@products_bp.route('/<product_code>', methods=['GET'])
@token_required
@permission_required('products', 'read')
def get_product(product_code):
    """
    Get specific product by product code
    
    Path Parameters:
        - product_code (str): The product code to retrieve
    
    Returns:
        JSON response with product details or 404 if not found
    """
    try:
        product = service.get_product_by_code(product_code)
        if product:
            return jsonify(product), 200
        else:
            return jsonify({"error": "Product not found"}), 404
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@products_bp.route('/<product_code>/related', methods=['GET'])
@token_required
@permission_required('products', 'read')
def get_related_products(product_code):
    """
    Get related/alternative products for cross-selling
    
    Path Parameters:
        - product_code (str): The base product code
    
    Query Parameters:
        - limit (int): Maximum number of related products (default: 5, max: 20)
    
    Returns:
        JSON response with array of related products
    """
    try:
        limit = request.args.get('limit', default=5, type=int)
        limit = min(limit, 20)  # Cap at 20 for performance
        
        related = service.get_related_products(product_code, limit=limit)
        return jsonify({
            "product_code": product_code,
            "related_products": related,
            "count": len(related)
        }), 200
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@products_bp.route('/statistics', methods=['GET'])
@token_required
@platform_user_required
def get_product_statistics():
    """
    Get product statistics and metrics (typically for admin dashboard)
    
    Note: This endpoint is restricted to platform users only
    
    Returns:
        JSON response with product statistics including:
        - summary: Total products, available, out of stock, low stock
        - by_category: Product count and average price by category
        - by_brand: Product count by brand (top 10)
        - price_distribution: Min, max, average, and median prices
    """
    try:
        stats = service.get_product_statistics()
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@products_bp.route('/autocomplete', methods=['GET'])
@token_required
@permission_required('products', 'read')
def autocomplete():
    """
    Get autocomplete suggestions for product search
    
    Query Parameters:
        - q, query, or search (str): Partial search string (minimum 2 characters)
        - limit (int): Maximum suggestions (default: 5, max: 10)
    
    Returns:
        JSON response with array of search suggestions
    """
    try:
        query = request.args.get('q') or request.args.get('query') or request.args.get('search')
        if not query or len(query) < 2:
            return jsonify({"suggestions": []}), 200
            
        limit = request.args.get('limit', default=5, type=int)
        limit = min(limit, 10)  # Cap at 10 suggestions
        
        suggestions = service.search_index.get_suggestions(query, max_suggestions=limit)
        return jsonify({"suggestions": suggestions}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@products_bp.route('/validate', methods=['POST'])
@token_required
@permission_required('products', 'create')
def validate_product():
    """
    Validate product data (typically used before creating/updating products)
    
    Request Body:
        JSON object with product data to validate
    
    Returns:
        JSON response with:
        - is_valid (bool): Whether the data is valid
        - errors (array): List of validation errors if any
    """
    try:
        product_data = request.get_json()
        if not product_data:
            return jsonify({
                "is_valid": False,
                "errors": ["No product data provided"]
            }), 400
            
        is_valid, errors = service.validate_product_data(product_data)
        return jsonify({
            "is_valid": is_valid,
            "errors": errors
        }), 200 if is_valid else 400
        
    except Exception as e:
        return jsonify({
            "is_valid": False,
            "errors": [str(e)]
        }), 500


# Error handlers
@products_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@products_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500