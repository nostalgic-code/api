from flask import Flask, request, jsonify, send_from_directory
import requests
from requests.auth import HTTPBasicAuth
from backend.pipeline.enhanced_pipeline import EnhancedDataPipeline
import os
from dotenv import load_dotenv
import threading

load_dotenv()

app = Flask(__name__)

# Configuration
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')
BASE_URL = os.getenv('API_BASE_URL')

@app.route('/fetch/<resource>', methods=['GET'])
def fetch_resource(resource):
    """Fetch data from external API (original functionality)"""
    url = f"{BASE_URL}/{resource}"
    query_params = request.args.to_dict()

    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            headers={"Accept": "application/json"},
            params=query_params,
            timeout=30
        )

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({
                "error": f"HTTP {response.status_code}",
                "message": response.reason
            }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Request failed", "message": str(e)}), 500

@app.route('/marketplace/stats', methods=['GET'])
def get_marketplace_stats():
    """Get marketplace statistics"""
    try:
        pipeline = EnhancedDataPipeline()
        stats = pipeline.get_marketplace_statistics()
        
        if stats:
            return jsonify(stats), 200
        else:
            return jsonify({"error": "Could not retrieve statistics"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/pipeline/sync/full', methods=['POST'])
def run_full_sync():
    """Trigger full synchronization"""
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

@app.route('/pipeline/sync/incremental', methods=['POST'])
def run_incremental_sync():
    """Trigger incremental synchronization"""
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

@app.route('/marketplace/products', methods=['GET'])
def get_marketplace_products():
    """Get products for marketplace with filtering"""
    try:
        from backend.app.utils.database import DatabaseConnection
        
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

@app.route('/dashboard')
def dashboard():
    """Serve the dashboard HTML file"""
    return send_from_directory('static', 'dashboard.html')

@app.route('/')
def home():
    return """
    <h1>Autospares Marketplace API</h1>
    <p><a href="/dashboard">🚗 Go to Dashboard</a></p>
    <h2>Data Pipeline Endpoints:</h2>
    <ul>
        <li><strong>POST /pipeline/sync/full</strong> - Run full synchronization</li>
        <li><strong>POST /pipeline/sync/incremental</strong> - Run incremental sync</li>
        <li><strong>GET /marketplace/stats</strong> - Get marketplace statistics</li>
        <li><strong>GET /marketplace/products</strong> - Get marketplace products with filtering</li>
    </ul>
    <h3>Product Search Parameters:</h3>
    <ul>
        <li>category, brand, min_price, max_price, search, available_only</li>
        <li>page, limit (pagination)</li>
    </ul>
    """

if __name__ == '__main__':
    app.run(debug=True)
