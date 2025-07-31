"""
Database Connection and Management Module

This module provides a simplified database connection handler for both MySQL and SQLite databases
with essential operations focused on connection management and query execution.

Key Features:
- MySQL and SQLite connection management with automatic environment detection
- Environment-based configuration for security
- Comprehensive error handling with specific error guidance
- Query execution with parameterized statements
- Connection testing and validation
- Simplified, focused responsibilities

Classes:
    DatabaseConnection: Main database connection handler

Dependencies:
    - mysql-connector-python: MySQL database connector (for production)
    - sqlite3: SQLite database (for development)
    - python-dotenv: Environment variable management
    - logging: For operation logging

Note:
    Schema management is now handled by Flask-Migrate.
    This module focuses on connection and query operations only.

Environment Variables:
    - FLASK_ENV: Environment mode (production uses MySQL, development uses SQLite)
    For MySQL (production):
        - DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
    For SQLite (development):
        - Uses same path as Flask app: backend/instance/pipeline_data.db

Usage:
    db = DatabaseConnection()
    if db.connect():
        results = db.execute_query("SELECT * FROM products")
        db.disconnect()

Author: Development Team
Version: 2.0
"""

import os
from dotenv import load_dotenv
import logging
from pathlib import Path

load_dotenv()

class DatabaseConnection:
    """
    Simplified database connection handler for both MySQL and SQLite.
    
    This class manages database connections based on environment and provides
    query execution capabilities with comprehensive error handling.
    
    Attributes:
        is_production (bool): Whether running in production mode
        connection: Active database connection object
        db_type (str): Database type ('mysql' or 'sqlite')
    """
    
    def __init__(self):
        """
        Initialize database connection parameters based on environment.
        
        Automatically detects environment and configures appropriate database type.
        Uses the same database path as Flask SQLAlchemy for consistency.
        """
        self.is_production = os.getenv('FLASK_ENV') == 'production'
        self.connection = None
        self.db_type = 'mysql' if self.is_production else 'sqlite'
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        if self.is_production:
            # MySQL configuration for production using DB_* environment variables
            self.host = os.getenv('DB_HOST')
            self.port = int(os.getenv('DB_PORT', 3306))
            self.database = os.getenv('DB_NAME')
            self.user = os.getenv('DB_USER')
            self.password = os.getenv('DB_PASSWORD')
            
            # Validate MySQL environment variables
            if not all([self.host, self.database, self.user]):
                missing = []
                if not self.host: missing.append('DB_HOST')
                if not self.database: missing.append('DB_NAME')
                if not self.user: missing.append('DB_USER')
                raise ValueError(f"Missing required MySQL environment variables: {', '.join(missing)}")
        else:
            # SQLite configuration for development - use same path as Flask app
            # Navigate to backend directory from application/utils/database.py
            current_file = Path(__file__)  # application/utils/database.py
            backend_dir = current_file.parent.parent.parent  # Go up to backend/
            instance_dir = backend_dir / 'instance'
            
            # Create instance directory if it doesn't exist
            instance_dir.mkdir(exist_ok=True)
            
            # Use the same database file as Flask SQLAlchemy
            self.database_path = str(instance_dir / 'pipeline_data.db')
            
            logging.info(f"SQLite database path: {self.database_path}")
            logging.info(f"Instance directory: {instance_dir}")
            logging.info(f"Backend directory: {backend_dir}")
    
    def connect(self):
        """
        Establish database connection based on environment configuration.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.is_production:
            return self._connect_mysql()
        else:
            return self._connect_sqlite()
    
    def _connect_mysql(self):
        """Connect to MySQL database for production environment."""
        try:
            import mysql.connector
            from mysql.connector import Error
            
            # Connection configuration
            config = {
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.user,
                'password': self.password,
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci',
                'autocommit': False,
                'raise_on_warnings': True,
                'use_unicode': True,
                'connection_timeout': 10,
                'sql_mode': 'TRADITIONAL'
            }
            
            logging.info(f"Attempting to connect to MySQL database at {self.host}:{self.port}")
            self.connection = mysql.connector.connect(**config)
            
            if self.connection.is_connected():
                # Test the connection with a simple query
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                
                db_info = self.connection.get_server_info()
                logging.info(f"Successfully connected to MySQL database. Server version: {db_info}")
                return True
                
        except Error as e:
            error_code = e.errno if hasattr(e, 'errno') else 'Unknown'
            logging.error(f"MySQL Error ({error_code}): {e}")
            
            # Provide specific error guidance
            if hasattr(e, 'errno'):
                if e.errno == 1045:
                    logging.error("Access denied - Check username and password")
                elif e.errno == 2003:
                    logging.error("Can't connect to MySQL server - Check host and port")
                elif e.errno == 1049:
                    logging.error("Unknown database - Check database name")
                elif e.errno == 2005:
                    logging.error("Unknown MySQL server host - Check hostname")
            
            return False
            
        except Exception as e:
            logging.error(f"Unexpected error connecting to MySQL database: {e}")
            return False
    
    def _connect_sqlite(self):
        """Connect to SQLite database for development environment."""
        try:
            import sqlite3
            
            # Ensure the directory exists before connecting
            db_dir = Path(self.database_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            logging.info(f"Attempting to connect to SQLite database: {self.database_path}")
            self.connection = sqlite3.connect(self.database_path)
            
            # Enable foreign key support for SQLite
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Test the connection with a simple query
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
            logging.info(f"Successfully connected to SQLite database: {self.database_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error connecting to SQLite database: {e}")
            logging.error(f"Database path: {self.database_path}")
            logging.error(f"Database directory exists: {Path(self.database_path).parent.exists()}")
            return False
    
    def disconnect(self):
        """
        Safely close the database connection.
        """
        if self.connection:
            if self.is_production and hasattr(self.connection, 'is_connected'):
                if self.connection.is_connected():
                    self.connection.close()
            else:
                self.connection.close()
            logging.info(f"Database connection closed ({self.db_type})")
    
    def execute_query(self, query, params=None):
        """
        Execute a SQL query with parameterized inputs for security.
        
        Args:
            query (str): SQL query string with placeholders
            params (tuple, optional): Parameters for query placeholders
            
        Returns:
            list: Query results for SELECT statements
            int: Number of affected rows for INSERT/UPDATE/DELETE
        """
        if not self.connection:
            raise Exception("No active database connection")
            
        cursor = None
        try:
            cursor = self.connection.cursor()
            
            # Handle parameter differences between MySQL and SQLite
            if params:
                if self.is_production:
                    # MySQL uses %s placeholders
                    cursor.execute(query, params)
                else:
                    # SQLite uses ? placeholders, convert if needed
                    if '%s' in query:
                        query = query.replace('%s', '?')
                    cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                self.connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            logging.error(f"Query: {query}")
            logging.error(f"Params: {params}")
            
            if self.connection:
                self.connection.rollback()
            raise
            
        finally:
            if cursor:
                cursor.close()
    
    def execute_transaction(self, queries_and_params):
        """
        Execute multiple queries as a single transaction.
        
        Args:
            queries_and_params (list): List of tuples containing (query, params)
            
        Returns:
            bool: True if all queries executed successfully
            
        Usage:
            db.execute_transaction([
                ("INSERT INTO users (name) VALUES (%s)", ("John",)),
                ("UPDATE users SET status = %s WHERE id = %s", ("active", 1))
            ])
        """
        if not self.connection:
            raise Exception("No active database connection")
            
        cursor = None
        try:
            cursor = self.connection.cursor()
            
            for query, params in queries_and_params:
                # Handle parameter differences between MySQL and SQLite
                if params and not self.is_production and '%s' in query:
                    query = query.replace('%s', '?')
                
                cursor.execute(query, params or ())
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logging.error(f"Error executing transaction: {e}")
            if self.connection:
                self.connection.rollback()
            raise
            
        finally:
            if cursor:
                cursor.close()
    
    def test_connection(self):
        """
        Comprehensive connection test with detailed database information.
        
        Tests database connectivity and gathers system information including
        current database, user permissions, and database version details.
        
        Returns:
            dict: Connection status and database information
        """
        try:
            if self.connect():
                cursor = self.connection.cursor()
                
                if self.is_production:
                    # Get database info for MySQL
                    cursor.execute("SELECT DATABASE()")
                    current_db = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT USER()")
                    current_user = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT VERSION()")
                    mysql_version = cursor.fetchone()[0]
                    
                    # Test basic permissions
                    test_table = "test_connection_permissions"
                    try:
                        cursor.execute(f"CREATE TABLE IF NOT EXISTS {test_table} (id INT)")
                        cursor.execute(f"DROP TABLE IF EXISTS {test_table}")
                        can_create_tables = True
                    except:
                        can_create_tables = False
                    
                    cursor.close()
                    self.disconnect()
                    
                    logging.info(f"MySQL connection test successful: {current_db}")
                    
                    return {
                        'connected': True,
                        'database': current_db,
                        'user': current_user,
                        'version': mysql_version,
                        'can_create_tables': can_create_tables,
                        'db_type': self.db_type
                    }
                else:
                    # SQLite connection test
                    cursor.execute("SELECT sqlite_version()")
                    sqlite_version = cursor.fetchone()[0]
                    
                    # Get database file size
                    db_size = Path(self.database_path).stat().st_size if Path(self.database_path).exists() else 0
                    
                    cursor.close()
                    self.disconnect()
                    
                    logging.info(f"SQLite connection test successful: {self.database_path}")
                    
                    return {
                        'connected': True,
                        'database': self.database_path,
                        'version': sqlite_version,
                        'db_type': self.db_type,
                        'can_create_tables': True,
                        'db_size_bytes': db_size
                    }
            else:
                return {'connected': False, 'db_type': self.db_type}
                
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return {'connected': False, 'error': str(e), 'db_type': self.db_type}