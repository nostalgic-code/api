from flask import Flask, request, jsonify
import requests
from requests.auth import HTTPBasicAuth
from data_pipeline import DataPipeline
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')
BASE_URL = os.getenv('API_BASE_URL')

@app.route('/fetch/<resource>', methods=['GET'])
def fetch_resource(resource):
    """
    Fetches data from an external API based on the resource name and optional query parameters.
    Example: /fetch/products?pagesize=100&pageno=1
    """
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
                "message": response.reason,
                "details": response.text
            }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Request failed", "message": str(e)}), 500

@app.route('/pipeline/run', methods=['POST'])
def run_pipeline():
    """Trigger the data pipeline manually"""
    try:
        data = request.json or {}
        resource = data.get('resource', 'products')
        page_size = data.get('page_size', 100)
        max_pages = data.get('max_pages')
        
        pipeline = DataPipeline()
        success = pipeline.run_pipeline(
            resource=resource, 
            page_size=page_size, 
            max_pages=max_pages
        )
        
        if success:
            return jsonify({"message": "Pipeline completed successfully"}), 200
        else:
            return jsonify({"error": "Pipeline failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/pipeline/status', methods=['GET'])
def pipeline_status():
    """Get pipeline status and database statistics"""
    try:
        pipeline = DataPipeline()
        stats = pipeline.get_product_statistics()
        
        if stats:
            return jsonify({
                "status": "connected",
                "statistics": stats
            }), 200
        else:
            return jsonify({"error": "Could not connect to database"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Root route for sanity check
@app.route('/')
def home():
    return """
    <h1>Flask API with Data Pipeline</h1>
    <p>Available endpoints:</p>
    <ul>
        <li><strong>GET /fetch/&lt;resource&gt;</strong> - Fetch data from external API</li>
        <li><strong>POST /pipeline/run</strong> - Run data pipeline manually</li>
        <li><strong>GET /pipeline/status</strong> - Get pipeline status and statistics</li>
    </ul>
    """

# Run the server
if __name__ == '__main__':
    app.run(debug=True)
