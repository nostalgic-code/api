"""
Application Package Initialization

This module initializes the Flask application components and makes
the database instance available to all modules.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration using the config dictionary
    from application.config import config
    config_name = config_name or 'development'
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={
        r"/api/*": {

            "origins": ["http://localhost:5000", "http://127.0.0.1:5000", "https://zezwebox.co.za", "https://www.zezwebox.co.za", "zezwebox.co.za"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Import models to ensure they're registered with SQLAlchemy
    with app.app_context():
        # Import all models
        from application.models import (
            customer, customer_user, platform_user,
            user_otp, user_session, product,
            depot, permission_code
        )
    
    # Register blueprints
    from application.api.auth import auth_bp
    from application.api.pipeline import pipeline_bp
    from application.api.common import common_bp
    from application.api.admin import admin_bp
    from application.api.frontend import frontend_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')  # Add /api prefix
    app.register_blueprint(pipeline_bp, url_prefix='/api/pipeline')  # Add /api prefix
    app.register_blueprint(common_bp, url_prefix='/api')  # Add /api prefix
    app.register_blueprint(admin_bp, url_prefix='/api/admin')  # Already has /api
    app.register_blueprint(frontend_bp)
    
    return app

# Make commonly used imports available at package level
__all__ = ['db', 'migrate', 'create_app']
