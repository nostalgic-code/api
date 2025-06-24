"""
Flask API Backend Application

This module serves as the main entry point for the Flask-based API backend service.
"""

import os
import sys
import logging
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the create_app function from application package
from application import create_app

# Create the app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

# Configure logging
def configure_logging():
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
    
    # File handler for production
    if not app.config['DEBUG']:
        file_handler = logging.FileHandler('app.log')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.ERROR)
        app.logger.addHandler(file_handler)

# Configure logging
configure_logging()

# Register error handlers
@app.errorhandler(404)
def not_found_error(error):
    return {"error": "Resource not found", "code": 404}, 404

@app.errorhandler(500)
def internal_error(error):
    from application import db
    db.session.rollback()
    app.logger.error(f"Internal error: {error}")
    return {"error": "Internal server error", "code": 500}, 500

@app.errorhandler(Exception)
def unhandled_exception(error):
    from application import db
    db.session.rollback()
    app.logger.error(f"Unhandled exception: {error}", exc_info=True)
    if app.config['DEBUG']:
        return {"error": str(error), "code": 500}, 500
    return {"error": "An unexpected error occurred", "code": 500}, 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AUTOSPARES MARKETPLACE API")
    print("="*60)
    
    # Display server information
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
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
