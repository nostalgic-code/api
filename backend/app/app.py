"""
Flask API Backend Application

This module serves as the main entry point for the Flask-based API backend service.
It provides a RESTful API interface for handling requests and communicating with
external services using HTTP Basic Authentication.

Key Features:
- Flask web framework for API endpoints
- Environment-based configuration management
- HTTP Basic Authentication for external API calls
- Thread-safe request handling capabilities

Dependencies:
- Flask: Web framework for creating API endpoints
- requests: HTTP library for making external API calls
- python-dotenv: Environment variable management
- threading: For concurrent request processing

Environment Variables Required:
- API_USERNAME: Username for external API authentication
- API_PASSWORD: Password for external API authentication  
- API_BASE_URL: Base URL for external API endpoints

Usage:
    python app.py

Author: Development Team
Version: 1.0
"""

from flask import Flask, request, jsonify, send_from_directory
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import threading
import os

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application instance
app = Flask(__name__)

# API Configuration - Loaded from environment variables for security
# These credentials are used for authenticating with external APIs
USERNAME = os.getenv('API_USERNAME')  # External API username
PASSWORD = os.getenv('API_PASSWORD')  # External API password
BASE_URL = os.getenv('API_BASE_URL')  # Base URL for external API endpoints

# Import API blueprints
from api.products import products_bp
from api.pipeline import pipeline_bp
from api.auth import auth_bp
from utils.database import DatabaseConnection

# Register API blueprints
app.register_blueprint(products_bp, url_prefix='/api/products')
app.register_blueprint(pipeline_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')

# CORS configuration for cross-origin requests
@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring application status.
    
    Returns:
        JSON: Application health status and basic info
    """
    try:
        # Test database connection
        db = DatabaseConnection()
        db_status = db.test_connection()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connected": db_status.get('connected', False),
                "database": db_status.get('database', 'unknown')
            },
            "environment": {
                "api_configured": bool(USERNAME and PASSWORD and BASE_URL)
            }
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    """
    Root endpoint providing API information.
    
    Returns:
        JSON: Basic API information and available endpoints
    """
    return jsonify({
        "message": "Marketplace API Backend",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "products": "/api/products",
            "pipeline": "/api/pipeline"
        },
        "documentation": "See individual endpoint documentation for details"
    })

# Generic API test endpoint
@app.route('/api/test', methods=['GET'])
def api_test():
    """
    Test endpoint for API connectivity verification.
    
    Returns:
        JSON: Test response with request information
    """
    return jsonify({
        "message": "API is working",
        "method": request.method,
        "timestamp": datetime.now().isoformat(),
        "headers": dict(request.headers),
        "args": dict(request.args)
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return jsonify({
        "error": "Not Found",
        "message": "The requested resource was not found",
        "status_code": 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors"""
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "status_code": 500
    }), 500

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors"""
    return jsonify({
        "error": "Bad Request",
        "message": "The request was malformed or invalid",
        "status_code": 400
    }), 400

# Application configuration
def configure_app():
    """Configure Flask application settings"""
    # Set JSON configuration
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # Security configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration validation
    required_db_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_db_vars = [var for var in required_db_vars if not os.getenv(var)]
    
    if missing_db_vars:
        print(f"Warning: Missing database environment variables: {', '.join(missing_db_vars)}")
    
    # API configuration validation
    required_api_vars = ['API_USERNAME', 'API_PASSWORD', 'API_BASE_URL']
    missing_api_vars = [var for var in required_api_vars if not os.getenv(var)]
    
    if missing_api_vars:
        print(f"Warning: Missing API environment variables: {', '.join(missing_api_vars)}")

# Initialize application
def create_app():
    """
    Application factory pattern for creating Flask app instances.
    
    Returns:
        Flask: Configured Flask application instance
    """
    configure_app()
    
    # Test database connection on startup
    try:
        db = DatabaseConnection()
        connection_result = db.test_connection()
        if connection_result.get('connected'):
            print(f"✓ Database connection successful: {connection_result.get('database')}")
        else:
            print("✗ Database connection failed")
            print("  Please check your database configuration")
    except Exception as e:
        print(f"✗ Database connection error: {e}")
    
    return app

# Add datetime import for health check
from datetime import datetime

# Development server configuration
if __name__ == '__main__':
    # Create and configure application
    app = create_app()
    
    # Development server settings
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print(f"Starting Flask development server...")
    print(f"Debug mode: {debug_mode}")
    print(f"Server: http://{host}:{port}")
    print(f"Health check: http://{host}:{port}/health")
    print(f"API docs: http://{host}:{port}/")
    
    # Start development server
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True  # Enable threading for concurrent requests
    )

