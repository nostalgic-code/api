"""
Application Configuration Module

This module contains configuration classes for different environments.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # SQLAlchemy configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ECHO = False
    
    # API Configuration
    API_USERNAME = os.getenv('API_USERNAME')
    API_PASSWORD = os.getenv('API_PASSWORD')
    API_BASE_URL = os.getenv('API_BASE_URL')
    
    # Authentication configuration
    OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', 5))
    OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', 3))
    SESSION_EXPIRY_HOURS = int(os.getenv('SESSION_EXPIRY_HOURS', 24))
    
    # SMS Configuration (for future implementation)
    SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'mock')  # 'twilio', 'aws_sns', 'mock'
    SMS_API_KEY = os.getenv('SMS_API_KEY')
    SMS_API_SECRET = os.getenv('SMS_API_SECRET')
    SMS_FROM_NUMBER = os.getenv('SMS_FROM_NUMBER')
    
    @staticmethod
    def init_app(app):
        """Initialize application with this config"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # SQLite database for development
    backend_dir = Path(__file__).parent.parent
    instance_dir = backend_dir / 'instance'
    instance_dir.mkdir(exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{instance_dir}/pipeline_data.db'
    SQLALCHEMY_ECHO = True  # Log all SQL statements

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # MySQL database for production
    MYSQL_USER = os.getenv('DB_USER', 'root')
    MYSQL_PASSWORD = os.getenv('DB_PASSWORD', '')
    MYSQL_HOST = os.getenv('DB_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('DB_PORT', 3306))
    MYSQL_DB = os.getenv('DB_NAME', 'autospares_marketplace')
    
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@'
        f'{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4'
    )
    
    # Production-specific settings
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_MAX_OVERFLOW = 20
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization"""
        Config.init_app(app)
        
        # Validate required environment variables
        required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'SECRET_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}