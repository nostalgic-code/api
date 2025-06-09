from flask import Flask, request, jsonify
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

# Configuration
USERNAME = "d5900938-be95-4412-95b3-50b11983e13e"
PASSWORD = "90fa0de5-250a-4e99-bd65-85b1854d9c82"
BASE_URL = "http://102.33.60.228:9183/getResources"

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

# Root route for sanity check
@app.route('/')
def home():
    return "Flask API is running. Use /fetch/<resource>"

# Run the server
if __name__ == '__main__':
    app.run(debug=True)
