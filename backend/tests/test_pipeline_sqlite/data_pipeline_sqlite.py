import requests
from requests.auth import HTTPBasicAuth
import json
import logging
from datetime import datetime
from backend.app.utils.database_sqlite import SQLiteConnection
import os
from dotenv import load_dotenv

load_dotenv()

class DataPipelineSQLite:
    def __init__(self, db_path=None):
        self.username = os.getenv('API_USERNAME')
        self.password = os.getenv('API_PASSWORD')
        self.base_url = os.getenv('API_BASE_URL')
        self.db = SQLiteConnection(db_path)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pipeline_sqlite.log'),
                logging.StreamHandler()
            ]
        )
        
        # Validate required environment variables
        if not all([self.username, self.password, self.base_url]):
            raise ValueError("Missing required environment variables")
    
    def fetch_data_from_api(self, resource, params=None):
        """Fetch data from the external API"""
        url = f"{self.base_url}/{resource}"
        
        try:
            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.username, self.password),
                headers={"Accept": "application/json"},
                params=params or {},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract products array from response
                products = data.get('products', [])
                logging.info(f"Successfully fetched {len(products)} products from API")
                return products
            else:
                logging.error(f"API request failed: {response.status_code} - {response.reason}")
                return []
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            return []
    
    def create_products_table(self):
        """Create products table schema for SQLite"""
        schema = """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uri TEXT,
            product_code TEXT NOT NULL UNIQUE,
            allocated_qty INTEGER DEFAULT 0,
            base_retail REAL DEFAULT 0.00,
            branch_code TEXT,
            brand TEXT,
            category TEXT,
            created_date TEXT,
            cross_reference_number TEXT,
            description TEXT,
            discount TEXT,
            group_name TEXT,
            linked_to TEXT,
            oem_number TEXT,
            origin TEXT,
            popular_number_one TEXT,
            popular_number_two TEXT,
            popular_number_three TEXT,
            qoh INTEGER DEFAULT 0,
            retail TEXT,
            special_offer_id TEXT,
            special_price TEXT,
            type TEXT,
            u2version TEXT,
            unit_price TEXT,
            uom TEXT,
            vat_category TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        """
        self.db.create_table_if_not_exists('products', schema)
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_category ON products(category)",
            "CREATE INDEX IF NOT EXISTS idx_branch_code ON products(branch_code)", 
            "CREATE INDEX IF NOT EXISTS idx_brand ON products(brand)",
            "CREATE INDEX IF NOT EXISTS idx_product_code ON products(product_code)"
        ]
        
        for index_query in indexes:
            try:
                self.db.execute_query(index_query)
            except Exception as e:
                logging.warning(f"Could not create index: {e}")
    
    def safe_decimal(self, value, default=0.00):
        """Safely convert value to float for SQLite"""
        try:
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return float(default)
            return float(value)
        except (ValueError, TypeError):
            return float(default)
    
    def safe_int(self, value, default=0):
        """Safely convert value to int"""
        try:
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return default
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    def insert_or_update_products(self, products):
        """Insert or update products in the SQLite database"""
        if not products:
            logging.warning("No products to insert")
            return 0
        
        inserted_count = 0
        updated_count = 0
        error_count = 0
        
        for product in products:
            try:
                product_code = product.get('product_code')
                if not product_code:
                    logging.warning(f"Product without product_code skipped: {product}")
                    error_count += 1
                    continue
                
                # Check if product exists
                check_query = "SELECT id FROM products WHERE product_code = ?"
                existing = self.db.execute_query(check_query, (product_code,))
                
                # Prepare common parameters
                params = [
                    product.get('@uri', ''),
                    self.safe_int(product.get('allocated_qty')),
                    self.safe_decimal(product.get('base_retail')),
                    product.get('branch_code', ''),
                    product.get('brand', ''),
                    product.get('category', ''),
                    product.get('created_date', ''),
                    json.dumps(product.get('cross_reference_number', [])),
                    product.get('description', ''),
                    json.dumps(product.get('discount', [])),
                    product.get('group', ''),
                    json.dumps(product.get('linked_to', [])),
                    product.get('oem_number', ''),
                    product.get('origin', ''),
                    product.get('popular_number_one', ''),
                    product.get('popular_number_two', ''),
                    product.get('popular_number_three', ''),
                    self.safe_int(product.get('qoh')),
                    json.dumps(product.get('retail', [])),
                    product.get('special_offer_id', ''),
                    product.get('special_price', ''),
                    product.get('type', ''),
                    product.get('u2version', ''),
                    json.dumps(product.get('unit_price', [])),
                    product.get('uom', ''),
                    product.get('vat_category', '')
                ]
                
                if existing:
                    # Update existing product
                    update_query = """
                    UPDATE products SET
                        uri = ?, allocated_qty = ?, base_retail = ?, branch_code = ?,
                        brand = ?, category = ?, created_date = ?, cross_reference_number = ?,
                        description = ?, discount = ?, group_name = ?, linked_to = ?,
                        oem_number = ?, origin = ?, popular_number_one = ?, popular_number_two = ?,
                        popular_number_three = ?, qoh = ?, retail = ?, special_offer_id = ?,
                        special_price = ?, type = ?, u2version = ?, unit_price = ?,
                        uom = ?, vat_category = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE product_code = ?
                    """
                    params.append(product_code)
                    self.db.execute_query(update_query, params)
                    updated_count += 1
                else:
                    # Insert new product
                    insert_query = """
                    INSERT INTO products (
                        uri, product_code, allocated_qty, base_retail, branch_code, brand,
                        category, created_date, cross_reference_number, description, discount,
                        group_name, linked_to, oem_number, origin, popular_number_one,
                        popular_number_two, popular_number_three, qoh, retail, special_offer_id,
                        special_price, type, u2version, unit_price, uom, vat_category
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    params.insert(1, product_code)
                    self.db.execute_query(insert_query, params)
                    inserted_count += 1
                
            except Exception as e:
                logging.error(f"Error processing product {product.get('product_code', 'unknown')}: {e}")
                error_count += 1
                continue
        
        logging.info(f"Processed products - Inserted: {inserted_count}, Updated: {updated_count}, Errors: {error_count}")
        return inserted_count + updated_count
    
    def run_pipeline(self, resource='products', page_size=100, max_pages=None):
        """Run the complete data pipeline"""
        logging.info(f"Starting SQLite data pipeline for resource: {resource}")
        
        # Connect to database
        if not self.db.connect():
            logging.error("Failed to connect to SQLite database")
            return False
        
        try:
            # Create table if needed
            if resource == 'products':
                self.create_products_table()
            
            total_records = 0
            page_no = 1
            consecutive_empty_pages = 0
            
            while True:
                # Fetch data with pagination
                params = {
                    'pagesize': page_size,
                    'pageno': page_no
                }
                
                logging.info(f"Fetching page {page_no} with page size {page_size}")
                products = self.fetch_data_from_api(resource, params)
                
                if not products:
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= 3:
                        logging.info("No more data to fetch")
                        break
                else:
                    consecutive_empty_pages = 0
                    # Insert data into database
                    count = self.insert_or_update_products(products)
                    total_records += count
                
                # Check if we've reached the end or hit max pages
                if len(products) < page_size or (max_pages and page_no >= max_pages):
                    break
                
                page_no += 1
            
            logging.info(f"SQLite Pipeline completed. Total records processed: {total_records}")
            return True
            
        except Exception as e:
            logging.error(f"SQLite Pipeline failed: {e}")
            return False
        finally:
            self.db.disconnect()
    
    def get_product_statistics(self):
        """Get basic statistics about products in database"""
        if not self.db.connect():
            return None
        
        try:
            stats = {}
            
            # Total products
            result = self.db.execute_query("SELECT COUNT(*) as total FROM products")
            stats['total_products'] = result[0][0] if result else 0
            
            # Products by category
            result = self.db.execute_query("""
                SELECT category, COUNT(*) as count 
                FROM products 
                WHERE category != '' 
                GROUP BY category 
                ORDER BY count DESC 
                LIMIT 10
            """)
            stats['top_categories'] = [{'category': row[0], 'count': row[1]} for row in result] if result else []
            
            # Products by branch
            result = self.db.execute_query("""
                SELECT branch_code, COUNT(*) as count 
                FROM products 
                WHERE branch_code != '' 
                GROUP BY branch_code 
                ORDER BY count DESC
            """)
            stats['branches'] = [{'branch': row[0], 'count': row[1]} for row in result] if result else []
            
            # Database file size
            db_size = os.path.getsize(self.db.db_path) if os.path.exists(self.db.db_path) else 0
            stats['database_size_mb'] = round(db_size / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return None
        finally:
            self.db.disconnect()