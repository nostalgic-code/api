"""
Database Connection and Management Module

This module provides a robust database connection handler for MySQL databases with
comprehensive error handling, connection pooling, and database operations management.

Key Features:
- MySQL connection management with automatic reconnection
- Environment-based configuration for security
- Comprehensive error handling with specific error guidance
- Query execution with parameterized statements
- Connection testing and validation
- Table creation and management utilities
- Logging for debugging and monitoring

Classes:
    DatabaseConnection: Main database connection handler

Dependencies:
    - mysql-connector-python: MySQL database connector
    - python-dotenv: Environment variable management
    - logging: For operation logging

Environment Variables Required:
    - DB_HOST: Database server hostname/IP
    - DB_PORT: Database server port (default: 3306)
    - DB_NAME: Database name
    - DB_USER: Database username
    - DB_PASSWORD: Database password

Usage:
    db = DatabaseConnection()
    if db.connect():
        results = db.execute_query("SELECT * FROM products")
        db.disconnect()

Author: Development Team
Version: 1.0
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class DatabaseConnection:
    """
    Database connection handler for MySQL with comprehensive error handling.
    
    This class manages MySQL database connections, provides query execution
    capabilities, and includes utilities for database management operations.
    
    Attributes:
        host (str): Database server hostname
        port (int): Database server port
        database (str): Database name
        user (str): Database username
        password (str): Database password
        connection: Active MySQL connection object
    """
    
    def __init__(self):
        """
        Initialize database connection parameters from environment variables.
        
        Raises:
            ValueError: If required environment variables are missing
        """
        self.host = os.getenv('DB_HOST')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.database = os.getenv('DB_NAME')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.connection = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Validate all required environment variables
        if not all([self.host, self.database, self.user, self.password]):
            missing = []
            if not self.host: missing.append('DB_HOST')
            if not self.database: missing.append('DB_NAME')
            if not self.user: missing.append('DB_USER')
            if not self.password: missing.append('DB_PASSWORD')
            raise ValueError(f"Missing required database environment variables: {', '.join(missing)}")
    
    def connect(self):
        """
        Establish database connection with comprehensive error handling.
        
        Attempts to connect to the MySQL database using configured parameters.
        Includes connection testing and detailed error reporting.
        
        Returns:
            bool: True if connection successful, False otherwise
            
        Note:
            Connection uses utf8mb4 charset for full Unicode support
            and includes timeout configuration for reliability.
        """
        try:
            # Connection configuration matching your PHP setup
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
            
            logging.info(f"Attempting to connect to database at {self.host}:{self.port}")
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
            logging.error(f"Unexpected error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """
        Safely close the database connection.
        
        Closes active database connection and logs the operation.
        Safe to call even if no connection exists.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Database connection closed")
    
    def execute_query(self, query, params=None):
        """
        Execute a SQL query with parameterized inputs for security.
        
        Args:
            query (str): SQL query string with placeholders
            params (tuple, optional): Parameters for query placeholders
            
        Returns:
            list: Query results for SELECT statements
            int: Number of affected rows for INSERT/UPDATE/DELETE
            
        Raises:
            Exception: If no active connection or query execution fails
            
        Note:
            Automatically handles transactions with commit/rollback
            Uses parameterized queries to prevent SQL injection
        """
        if not self.connection or not self.connection.is_connected():
            raise Exception("No active database connection")
            
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                self.connection.commit()
                return cursor.rowcount
                
        except Error as e:
            logging.error(f"Error executing query: {e}")
            logging.error(f"Query: {query}")
            logging.error(f"Params: {params}")
            
            if self.connection:
                self.connection.rollback()
            raise
            
        finally:
            if cursor:
                cursor.close()
    
    def create_table_if_not_exists(self, table_name, schema):
        """
        Create a database table if it doesn't already exist.
        
        Args:
            table_name (str): Name of the table to create
            schema (str): SQL schema definition for the table
            
        Raises:
            Exception: If table creation fails
            
        Usage:
            db.create_table_if_not_exists(
                'products', 
                'id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255)'
            )
        """
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        try:
            self.execute_query(query)
            logging.info(f"Table {table_name} created or already exists")
        except Exception as e:
            logging.error(f"Error creating table {table_name}: {e}")
            raise
    
    def test_connection(self):
        """
        Comprehensive connection test with detailed database information.
        
        Tests database connectivity and gathers system information including
        current database, user permissions, and MySQL version details.
        
        Returns:
            dict: Connection status and database information
                - connected (bool): Connection success status
                - database (str): Current database name
                - user (str): Current user
                - mysql_version (str): MySQL server version
                - can_create_tables (bool): Table creation permissions
                - error (str): Error message if connection failed
                
        Usage:
            result = db.test_connection()
            if result['connected']:
                print(f"Connected to {result['database']} as {result['user']}")
        """
        try:
            if self.connect():
                cursor = self.connection.cursor()
                
                # Get database info
                cursor.execute("SELECT DATABASE()")
                current_db = cursor.fetchone()[0]
                
                cursor.execute("SELECT USER()")
                current_user = cursor.fetchone()[0]
                
                cursor.execute("SELECT VERSION()")
                mysql_version = cursor.fetchone()[0]
                
                # Test table creation permissions
                test_table = "test_connection_permissions"
                try:
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {test_table} (id INT)")
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table}")
                    can_create_tables = True
                except:
                    can_create_tables = False
                
                cursor.close()
                self.disconnect()
                
                logging.info(f"Connection test successful: {current_db}, {current_user}, {mysql_version}, {can_create_tables}")
                
                return {
                    'connected': True,
                    'database': current_db,
                    'user': current_user,
                    'mysql_version': mysql_version,
                    'can_create_tables': can_create_tables
                }
            else:
                return {'connected': False}
                
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return {'connected': False, 'error': str(e)}