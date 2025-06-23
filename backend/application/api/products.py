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
    GET /products/<product_code> - Get specific product details
    GET /products/search - Search products by query
    GET /products/categories - List available categories
    GET /products/brands - List available brands

Dependencies:
    - Flask Blueprint for route organization
    - Product service layer for business logic
    - Database utilities for data access
    - Validation utilities for input validation

Usage:
    from app.api.products import products_bp
    app.register_blueprint(products_bp)

Author: Development Team
Version: 1.0
"""

from flask import Blueprint, request, jsonify
from application.services.product_service import ProductService

products_bp = Blueprint('products', __name__, url_prefix='/products')
service = ProductService()


@products_bp.route('/', methods=['GET'])
def get_products():
    """Get paginated list of products with optional filtering"""
    try:
        # Parse filters and pagination from query params
        filters = {
            "available_only": request.args.get('available_only', 'true').lower() == 'true',
            "category": request.args.get('category'),
            "brand": request.args.get('brand'),
            "min_price": request.args.get('min_price', type=float),
            "max_price": request.args.get('max_price', type=float),
            "search": request.args.get('search')
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        pagination = {
            "page": request.args.get('page', default=1, type=int),
            "limit": request.args.get('limit', default=20, type=int)
        }

        result = service.get_products(filters=filters, pagination=pagination)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


@products_bp.route('/<product_code>', methods=['GET'])
def get_product(product_code):
    """Get specific product by product code"""
    try:
        product = service.get_product_by_code(product_code)
        if product:
            return jsonify(product), 200
        else:
            return jsonify({"error": "Product not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/search', methods=['GET'])
def search_products():
    """Search products by description, brand, or category"""
    try:
        query = request.args.get('q') or request.args.get('query') or request.args.get('search')
        if not query:
            return jsonify({"error": "Search query parameter 'q' or 'query' or 'search' is required"}), 400

        filters = {
            "available_only": request.args.get('available_only', 'true').lower() == 'true',
            "category": request.args.get('category'),
            "brand": request.args.get('brand'),
            "min_price": request.args.get('min_price', type=float),
            "max_price": request.args.get('max_price', type=float)
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        result = service.search_products(query, filters=filters)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get list of available product categories"""
    try:
        categories = service.get_categories()
        return jsonify({"categories": categories}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/brands', methods=['GET'])
def get_brands():
    """Get list of available product brands"""
    try:
        brands = service.get_brands()
        return jsonify({"brands": brands}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/autocomplete', methods=['GET'])
def autocomplete():
    """
    Autocomplete product search suggestions.
    Query param: q (partial search string)
    """
    try:
        query = request.args.get('q') or request.args.get('query') or request.args.get('search')
        if not query or len(query) < 2:
            return jsonify({"suggestions": []}), 200
        suggestions = service.search_index.get_suggestions(query)
        return jsonify({"suggestions": suggestions}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500