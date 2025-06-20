"""
Flask API Backend Application

This module serves as the main entry point for the Flask-based API backend service.
It provides a RESTful API interface for handling requests and communicating with
external services using HTTP Basic Authentication.
"""

import os
import sys
import logging
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the backend directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import db from application package
from application import db
from application.config import DevelopmentConfig, ProductionConfig

# Initialize migrate
migrate = Migrate()

def create_app(config_name=None):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    if config_name == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS properly
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables within app context
    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        from application.models import user, user_otp, user_session, product
        
        # Create tables if they don't exist
        db.create_all()
        
        app.logger.info(f"Database initialized: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    return app

def configure_logging(app):
    """Configure application logging"""
    # Remove default Flask logger handlers
    app.logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Set log level based on environment
    if app.config['DEBUG']:
        app.logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(console_handler)
    
    # Optionally add file handler for production
    if not app.config['DEBUG']:
        file_handler = logging.FileHandler('app.log')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.ERROR)
        app.logger.addHandler(file_handler)

def register_blueprints(app):
    """Register all application blueprints"""
    # Import blueprints
    from application.api.auth import auth_bp
    from application.api.pipeline import pipeline_bp
    from application.api.common import common_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pipeline_bp, url_prefix='/pipeline')
    app.register_blueprint(common_bp)  # Common routes like health, schema, etc.
    
    app.logger.info("Blueprints registered successfully")

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {"error": "Resource not found", "code": 404}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal error: {error}")
        return {"error": "Internal server error", "code": 500}, 500
    
    @app.errorhandler(Exception)
    def unhandled_exception(error):
        db.session.rollback()
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        if app.config['DEBUG']:
            return {"error": str(error), "code": 500}, 500
        return {"error": "An unexpected error occurred", "code": 500}, 500

# Create the app instance
app = create_app()

if __name__ == '__main__':
    # Test database connection on startup
    from application.utils.database import DatabaseConnection
    
    print("\n" + "="*60)
    print("🚀 AUTOSPARES MARKETPLACE API")
    print("="*60)
    
    # Test database connection
    try:
        db_conn = DatabaseConnection()
        db_test = db_conn.test_connection()
        
        if db_test.get('connected'):
            print(f"✓ Database: {db_test.get('database')}")
            print(f"✓ Type: {db_test.get('db_type')}")
            print(f"✓ Version: {db_test.get('version')}")
        else:
            print(f"✗ Database connection failed: {db_test.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Database test error: {e}")
    
    # Display server information
    print("\n" + "-"*60)
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    print(f"Server URL: http://127.0.0.1:5000")
    print("-"*60)
    print("\nAvailable Endpoints:")
    print("  • Health Check: http://127.0.0.1:5000/health")
    print("  • API Info: http://127.0.0.1:5000/")
    print("  • Schema Info: http://127.0.0.1:5000/schema")
    print("  • Auth API: http://127.0.0.1:5000/auth/*")
    print("  • Pipeline API: http://127.0.0.1:5000/pipeline/*")
    print("="*60 + "\n")
    
    # Run the application
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=app.config['DEBUG']
    )
