"""
Flask API Backend Application

This module serves as the main entry point for the Flask-based API backend service.
It provides a RESTful API interface for handling requests and communicating with
external services using HTTP Basic Authentication.
"""

import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configure app
    configure_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Make db available globally for models
    import application as app_module
    app_module.db = db
    
    # Import models after db is available
    with app.app_context():
        from application.models import user, user_otp, user_session, product
        # Create all database tables
        db.create_all()
    
    # Import and register blueprints after models are loaded
    from application.api.auth import auth_bp
    from application.api.pipeline import pipeline_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pipeline_bp)
    
    # Register routes
    register_routes(app)
    
    return app

def configure_app(app):
    """Configure Flask application settings"""
    # Set JSON configuration
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # Security configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration - environment-based switching
    if os.getenv('FLASK_ENV') == 'production':
        # MySQL for production - Using DB_* variables
        MYSQL_USER = os.getenv('DB_USER', 'root')
        MYSQL_PASSWORD = os.getenv('DB_PASSWORD', '')
        MYSQL_HOST = os.getenv('DB_HOST', 'localhost')
        MYSQL_DB = os.getenv('DB_NAME', 'autospares_marketplace')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
        
        # Validate required environment variables
        required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"Warning: Missing database environment variables: {', '.join(missing_vars)}")
    else:
        # SQLite for development - Create absolute path and ensure directory exists
        backend_dir = Path(__file__).parent  # Get backend directory
        instance_dir = backend_dir / 'instance'
        
        # Create instance directory if it doesn't exist
        instance_dir.mkdir(exist_ok=True)
        
        # Use absolute path for SQLAlchemy
        db_path = instance_dir / 'pipeline_data.db'
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        print(f"SQLite database will be created at: {db_path}")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # API configuration validation
    required_api_vars = ['API_USERNAME', 'API_PASSWORD', 'API_BASE_URL']
    missing_api_vars = [var for var in required_api_vars if not os.getenv(var)]
    if missing_api_vars:
        print(f"Warning: Missing API environment variables: {', '.join(missing_api_vars)}")

def register_routes(app):
    """Register application routes"""
    from application.utils.database import DatabaseConnection
    
    # Configuration for external API
    USERNAME = os.getenv('API_USERNAME')
    PASSWORD = os.getenv('API_PASSWORD')
    BASE_URL = os.getenv('API_BASE_URL')
    
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
        """Health check endpoint for monitoring application status."""
        try:
            # Test database connection using unified DatabaseConnection
            db_conn = DatabaseConnection()
            db_status = db_conn.test_connection()
            
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": {
                    "connected": db_status.get('connected', False),
                    "database": db_status.get('database', 'unknown'),
                    "type": db_status.get('db_type', 'unknown'),
                    "version": db_status.get('version', 'unknown'),
                    "can_create_tables": db_status.get('can_create_tables', False)
                },
                "environment": {
                    "flask_env": os.getenv('FLASK_ENV', 'development'),
                    "api_configured": bool(USERNAME and PASSWORD and BASE_URL),
                    "database_type": "MySQL" if os.getenv('FLASK_ENV') == 'production' else "SQLite"
                }
            }), 200
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

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

    @app.route('/dashboard')
    def dashboard():
        """Serve the dashboard HTML file"""
        return send_from_directory('static', 'dashboard.html')

    @app.route('/schema', methods=['GET'])
    def get_schema():
        """Get database schema information using unified DatabaseConnection"""
        try:
            from application.utils.database import DatabaseConnection
            
            db_conn = DatabaseConnection()
            schema_info = {
                "database_type": "MySQL" if db_conn.is_production else "SQLite",
                "database_uri": app.config['SQLALCHEMY_DATABASE_URI'],
                "tables": {}
            }
            
            if db_conn.connect():
                try:
                    if db_conn.is_production:
                        # MySQL specific queries
                        result = db_conn.execute_query("SHOW TABLES")
                        tables = [row[0] for row in result] if result else []
                        
                        for table in tables:
                            result = db_conn.execute_query(f"DESCRIBE {table}")
                            columns = []
                            for col in result:
                                columns.append({
                                    "name": col[0],
                                    "type": col[1],
                                    "null": col[2],
                                    "key": col[3],
                                    "default": col[4],
                                    "extra": col[5]
                                })
                            schema_info["tables"][table] = {"columns": columns}
                    else:
                        # SQLite specific queries
                        result = db_conn.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = [row[0] for row in result] if result else []
                        
                        for table in tables:
                            result = db_conn.execute_query(f"PRAGMA table_info({table})")
                            columns = []
                            for col in result:
                                columns.append({
                                    "name": col[1],
                                    "type": col[2],
                                    "not_null": bool(col[3]),
                                    "default": col[4],
                                    "primary_key": bool(col[5])
                                })
                            schema_info["tables"][table] = {"columns": columns}
                            
                finally:
                    db_conn.disconnect()
            
            return jsonify(schema_info), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/')
    def home():
        """Root endpoint providing API information and available endpoints"""
        return jsonify({
            "message": "Autospares Marketplace API",
            "version": "2.0",
            "endpoints": {
                "health": "/health",
                "auth": "/auth/*",
                "pipeline": "/pipeline/*",
                "dashboard": "/dashboard",
                "schema": "/schema"
            },
            "environment": os.getenv('FLASK_ENV', 'development'),
            "database": "MySQL" if os.getenv('FLASK_ENV') == 'production' else "SQLite"
        })

# Create the app instance for Flask CLI
app = create_app()

if __name__ == '__main__':
    # Test database connection on startup using unified DatabaseConnection
    try:
        from application.utils.database import DatabaseConnection
        db_conn = DatabaseConnection()
        db_test = db_conn.test_connection()
        
        if db_test.get('connected'):
            print(f"✓ Database connection successful: {db_test.get('database')} ({db_test.get('db_type')})")
            if db_test.get('can_create_tables'):
                print("✓ Database permissions: Can create tables")
            else:
                print("⚠ Database permissions: Limited access")
        else:
            print(f"✗ Database connection failed: {db_test.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"✗ Database connection error: {e}")
    
    # Start Flask application
    print("\n" + "="*50)
    print("🚀 Starting Flask Development Server")
    print("="*50)
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Database: {'MySQL' if os.getenv('FLASK_ENV') == 'production' else 'SQLite'}")
    print(f"Debug mode: {os.getenv('FLASK_ENV') != 'production'}")
    print(f"Server: http://127.0.0.1:5000")
    print(f"Health check: http://127.0.0.1:5000/health")
    print(f"Schema info: http://127.0.0.1:5000/schema")
    print(f"API docs: http://127.0.0.1:5000/")
    print("="*50)
    
    app.run(
        debug=os.getenv('FLASK_ENV') != 'production',
        host='127.0.0.1',
        port=5000
    )
