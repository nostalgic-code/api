"""
Pipeline API Module

This module provides RESTful API endpoints for managing data synchronization
pipeline operations. It allows triggering sync operations, monitoring progress,
and retrieving pipeline statistics through HTTP endpoints.

Key Features:
- Trigger full and incremental synchronization
- Background processing to prevent request timeouts
- Pipeline statistics and monitoring
- Configurable sync parameters
- Error handling and status reporting

Endpoints:
    POST /pipeline/sync/full - Trigger full product synchronization
    POST /pipeline/sync/incremental - Trigger incremental synchronization
    GET /pipeline/stats - Get pipeline statistics and metrics

Dependencies:
    - Flask Blueprint for route organization
    - EnhancedDataPipeline for sync operations
    - Threading for background processing

Request/Response Format:
    All endpoints use JSON for request/response data

Usage:
    from app.api.pipeline import pipeline_bp
    app.register_blueprint(pipeline_bp)

Example Requests:
    # Trigger full sync
    POST /pipeline/sync/full
    {
        "page_size": 100,
        "max_pages": 50
    }
    
    # Trigger incremental sync
    POST /pipeline/sync/incremental
    {
        "hours_back": 2
    }
    
    # Get statistics
    GET /pipeline/stats

Author: Development Team
Version: 1.0
"""

from flask import Blueprint, request, jsonify
import threading
from application.pipeline.enhanced_pipeline import EnhancedDataPipeline

# Create Blueprint for pipeline routes
pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/pipeline')

@pipeline_bp.route('/sync/full', methods=['POST'])
def run_full_sync():
    """
    Trigger full product synchronization.
    
    Initiates a complete synchronization of all products from the external API
    to the local database. Runs in background to prevent request timeouts.
    
    Request Body (JSON, optional):
        page_size (int): Number of products per API request (default: 100)
        max_pages (int): Maximum pages to process (default: unlimited)
    
    Returns:
        JSON: Success message with 200 status
        JSON: Error message with 500 status on failure
    
    Example:
        POST /pipeline/sync/full
        {
            "page_size": 50,
            "max_pages": 10
        }
        
        Response:
        {
            "message": "Full sync started successfully"
        }
    
    Note:
        Sync runs asynchronously - check logs or stats endpoint for progress
    """
    try:
        data = request.json or {}
        page_size = data.get('page_size', 100)
        max_pages = data.get('max_pages')
        
        # Run sync in background to avoid timeout
        def run_sync():
            pipeline = EnhancedDataPipeline()
            pipeline.run_full_sync(page_size=page_size, max_pages=max_pages)
        
        # Start sync in background thread
        threading.Thread(target=run_sync, daemon=True).start()
        
        return jsonify({"message": "Full sync started successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pipeline_bp.route('/sync/incremental', methods=['POST'])
def run_incremental_sync():
    """
    Trigger incremental product synchronization.
    
    Initiates a lightweight synchronization focusing on recent changes.
    Suitable for frequent execution to keep data current.
    
    Request Body (JSON, optional):
        hours_back (int): Hours to look back for changes (default: 1)
    
    Returns:
        JSON: Success message with 200 status
        JSON: Error message with 500 status on failure
    
    Example:
        POST /pipeline/sync/incremental
        {
            "hours_back": 2
        }
        
        Response:
        {
            "message": "Incremental sync started successfully"
        }
    
    Note:
        Sync runs asynchronously for non-blocking operation
    """
    try:
        data = request.json or {}
        hours_back = data.get('hours_back', 1)
        
        # Run sync in background to avoid timeout
        def run_sync():
            pipeline = EnhancedDataPipeline()
            pipeline.run_incremental_sync(hours_back=hours_back)
        
        # Start sync in background thread
        threading.Thread(target=run_sync, daemon=True).start()
        
        return jsonify({"message": "Incremental sync started successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pipeline_bp.route('/stats', methods=['GET'])
def get_pipeline_stats():
    """
    Get comprehensive pipeline statistics and metrics.
    
    Retrieves current marketplace statistics including product counts,
    price ranges, category distribution, and recent sync history.
    
    Returns:
        JSON: Statistics object with 200 status
        JSON: Error message with 500 status on failure
    
    Response Format:
        {
            "total_products": 1500,
            "available_products": 1200,
            "price_range": {
                "average": 45.67,
                "min": 1.99,
                "max": 999.99
            },
            "top_categories": [
                {"category": "Electronics", "count": 450},
                {"category": "Tools", "count": 320}
            ],
            "recent_syncs": [
                {
                    "type": "full",
                    "fetched": 1500,
                    "inserted": 50,
                    "updated": 120,
                    "errors": 2,
                    "completed": "2023-12-01T10:30:00",
                    "status": "completed"
                }
            ]
        }
    
    Usage:
        GET /pipeline/stats
    """
    try:
        pipeline = EnhancedDataPipeline()
        stats = pipeline.get_marketplace_statistics()
        
        if stats:
            return jsonify(stats), 200
        else:
            return jsonify({"error": "Could not retrieve statistics"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pipeline_bp.route('/marketplace/stats', methods=['GET'])
def get_marketplace_stats():
    """
    Get marketplace statistics.
    
    Retrieves comprehensive marketplace statistics including product counts,
    price information, and category distributions.
    
    Returns:
        JSON: Marketplace statistics with 200 status
        JSON: Error message with 500 status on failure
    """
    try:
        pipeline = EnhancedDataPipeline()
        stats = pipeline.get_marketplace_statistics()
        
        if stats:
            return jsonify(stats), 200
        else:
            return jsonify({"error": "Could not retrieve statistics"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pipeline_bp.route('/marketplace/products', methods=['GET'])
def get_marketplace_products():
    """
    Get products for marketplace with filtering.
    
    Retrieves marketplace products with support for filtering, searching,
    and pagination.
    
    Query Parameters:
        category (str): Filter by category
        brand (str): Filter by brand
        min_price (float): Minimum price filter
        max_price (float): Maximum price filter
        search (str): Search in description and brand
        available_only (bool): Show only available products (default: true)
        page (int): Page number for pagination (default: 1)
        limit (int): Items per page (default: 20)
    
    Returns:
        JSON: Products with pagination info and 200 status
        JSON: Error message with 500 status on failure
    """
    try:
        from application.utils.database import DatabaseConnection
        
        # Get query parameters
        category = request.args.get('category')
        brand = request.args.get('brand')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        search = request.args.get('search')
        available_only = request.args.get('available_only', 'true').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        db = DatabaseConnection()
        if not db.connect():
            return jsonify({"error": "Database connection failed"}), 500
        
        # Build query
        where_conditions = []
        params = []
        
        if available_only:
            where_conditions.append("is_available = TRUE")
        
        if category:
            where_conditions.append("category = %s")
            params.append(category)
        
        if brand:
            where_conditions.append("brand = %s")
            params.append(brand)
        
        if min_price is not None:
            where_conditions.append("current_price >= %s")
            params.append(min_price)
        
        if max_price is not None:
            where_conditions.append("current_price <= %s")
            params.append(max_price)
        
        if search:
            where_conditions.append("(description LIKE %s OR brand LIKE %s)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM marketplace_products WHERE {where_clause}"
        total_result = db.execute_query(count_query, params)
        total = total_result[0][0] if total_result else 0
        
        # Get products
        offset = (page - 1) * limit
        query = f"""
            SELECT product_code, description, category, brand, current_price, 
                   quantity_available, unit_of_measure, part_numbers
            FROM marketplace_products 
            WHERE {where_clause}
            ORDER BY brand, description
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        products = db.execute_query(query, params)
        
        result = {
            "products": [
                {
                    "product_code": row[0],
                    "description": row[1],
                    "category": row[2],
                    "brand": row[3],
                    "price": float(row[4]),
                    "quantity_available": row[5],
                    "unit_of_measure": row[6],
                    "part_numbers": row[7] if row[7] else []
                } for row in products
            ],
            "pagination": {
                "current_page": page,
                "total_pages": (total + limit - 1) // limit,
                "total_items": total,
                "items_per_page": limit
            }
        }
        
        db.disconnect()
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500