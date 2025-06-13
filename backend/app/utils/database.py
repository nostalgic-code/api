import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class DatabaseConnection:
    def __init__(self):
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
        """Establish database connection with better error handling"""
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
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Database connection closed")
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
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