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
from backend.app.pipeline import EnhancedDataPipeline

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