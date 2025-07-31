"""
Common API Routes

This module contains common routes like health check, schema info, etc.
"""

from flask import Blueprint, jsonify, current_app, send_from_directory
from datetime import datetime
import os

from application.utils.database import DatabaseConnection

# Create Blueprint
common_bp = Blueprint('common', __name__)

@common_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring application status."""
    try:
        # Test database connection
        db_conn = DatabaseConnection()
        db_status = db_conn.test_connection()
        
        # Get API configuration status
        api_configured = all([
            current_app.config.get('API_USERNAME'),
            current_app.config.get('API_PASSWORD'),
            current_app.config.get('API_BASE_URL')
        ])
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0",
            "environment": {
                "flask_env": os.getenv('FLASK_ENV', 'development'),
                "debug": current_app.config.get('DEBUG', False),
                "api_configured": api_configured
            },
            "database": {
                "connected": db_status.get('connected', False),
                "type": db_status.get('db_type', 'unknown'),
                "database": db_status.get('database', 'unknown'),
                "version": db_status.get('version', 'unknown')
            },
            "services": {
                "auth": "operational",
                "pipeline": "operational",
                "sms": current_app.config.get('SMS_PROVIDER', 'mock')
            }
        }
        
        # Determine overall health
        if not db_status.get('connected'):
            health_status['status'] = 'degraded'
            health_status['database']['error'] = db_status.get('error', 'Connection failed')
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

@common_bp.route('/', methods=['GET'])
def api_info():
    """Root endpoint providing API information and available endpoints"""
    return jsonify({
        "name": "Autospares Marketplace API",
        "version": "2.0",
        "description": "RESTful API for automotive parts marketplace",
        "documentation": {
            "swagger": "/docs",  # Future implementation
            "postman": "https://documenter.getpostman.com/..."  # Future
        },
        "endpoints": {
            "health": {
                "url": "/health",
                "methods": ["GET"],
                "description": "System health check"
            },
            "auth": {
                "base_url": "/auth",
                "endpoints": {
                    "send_otp": {"url": "/auth/send-otp", "method": "POST"},
                    "verify_otp": {"url": "/auth/verify-otp", "method": "POST"},
                    "validate_session": {"url": "/auth/validate-session", "method": "POST"},
                    "logout": {"url": "/auth/logout", "method": "POST"},
                    "user_info": {"url": "/auth/user-info", "method": "GET"}
                }
            },
            "pipeline": {
                "base_url": "/pipeline",
                "description": "Data pipeline operations"
            },
            "schema": {
                "url": "/schema",
                "methods": ["GET"],
                "description": "Database schema information"
            }
        },
        "environment": os.getenv('FLASK_ENV', 'development'),
        "contact": {
            "email": "support@autospares.com",
            "documentation": "https://docs.autospares.com"
        }
    })

@common_bp.route('/schema', methods=['GET'])
def get_schema():
    """Get database schema information"""
    try:
        db_conn = DatabaseConnection()
        schema_info = {
            "database_type": db_conn.db_type,
            "environment": os.getenv('FLASK_ENV', 'development'),
            "tables": {},
            "statistics": {
                "total_tables": 0,
                "total_columns": 0
            }
        }
        
        if db_conn.connect():
            try:
                if db_conn.is_production:
                    # MySQL schema query
                    tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()"
                    result = db_conn.execute_query(tables_query)
                    tables = [row[0] for row in result] if result else []
                    
                    for table in tables:
                        columns_query = """
                            SELECT column_name, data_type, is_nullable, column_key, 
                                   column_default, extra
                            FROM information_schema.columns 
                            WHERE table_schema = DATABASE() AND table_name = %s
                            ORDER BY ordinal_position
                        """
                        columns_result = db_conn.execute_query(columns_query, (table,))
                        
                        columns = []
                        for col in columns_result:
                            columns.append({
                                "name": col[0],
                                "type": col[1],
                                "nullable": col[2] == 'YES',
                                "key": col[3],
                                "default": col[4],
                                "extra": col[5]
                            })
                        
                        schema_info["tables"][table] = {
                            "columns": columns,
                            "column_count": len(columns)
                        }
                else:
                    # SQLite schema query
                    result = db_conn.execute_query(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                    tables = [row[0] for row in result] if result else []
                    
                    for table in tables:
                        result = db_conn.execute_query(f"PRAGMA table_info({table})")
                        columns = []
                        for col in result:
                            columns.append({
                                "name": col[1],
                                "type": col[2],
                                "nullable": not bool(col[3]),
                                "default": col[4],
                                "primary_key": bool(col[5])
                            })
                        
                        schema_info["tables"][table] = {
                            "columns": columns,
                            "column_count": len(columns)
                        }
                
                # Calculate statistics
                schema_info["statistics"]["total_tables"] = len(schema_info["tables"])
                schema_info["statistics"]["total_columns"] = sum(
                    table_info["column_count"] 
                    for table_info in schema_info["tables"].values()
                )
                
            finally:
                db_conn.disconnect()
        else:
            return jsonify({
                "error": "Failed to connect to database",
                "database_type": db_conn.db_type
            }), 503
        
        return jsonify(schema_info), 200
        
    except Exception as e:
        current_app.logger.error(f"Schema retrieval error: {e}")
        return jsonify({
            "error": "Failed to retrieve schema",
            "message": str(e)
        }), 500

@common_bp.route('/dashboard')
def dashboard():
    """Serve the dashboard HTML file"""
    return send_from_directory('static', 'dashboard.html')