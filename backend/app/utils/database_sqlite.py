import sqlite3
import os
import logging
import json
from datetime import datetime

class SQLiteConnection:
    def __init__(self, db_path=None):
        self.db_path = db_path or 'pipeline_test.db'
        self.connection = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def connect(self):
        """Establish SQLite database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            
            # Enable foreign key constraints
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            logging.info(f"Successfully connected to SQLite database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Error connecting to SQLite: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logging.info("SQLite database connection closed")
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        if not self.connection:
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
                
        except sqlite3.Error as e:
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
        """Create table if it doesn't exist"""
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        try:
            self.execute_query(query)
            logging.info(f"Table {table_name} created or already exists")
        except Exception as e:
            logging.error(f"Error creating table {table_name}: {e}")
            raise
    
    def test_connection(self):
        """Test database connection and return detailed info"""
        try:
            if self.connect():
                cursor = self.connection.cursor()
                
                # Get SQLite version
                cursor.execute("SELECT sqlite_version()")
                sqlite_version = cursor.fetchone()[0]
                
                # Check if database file exists and get size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                # Test table creation permissions
                test_table = "test_connection_permissions"
                try:
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {test_table} (id INTEGER PRIMARY KEY)")
                    cursor.execute(f"DROP TABLE IF EXISTS {test_table}")
                    can_create_tables = True
                except:
                    can_create_tables = False
                
                cursor.close()
                self.disconnect()
                
                return {
                    'connected': True,
                    'database': self.db_path,
                    'sqlite_version': sqlite_version,
                    'db_size_bytes': db_size,
                    'can_create_tables': can_create_tables
                }
            else:
                return {'connected': False}
                
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return {'connected': False, 'error': str(e)}