import requests
from requests.auth import HTTPBasicAuth
import json
import logging
from datetime import datetime
from database import DatabaseConnection
import os
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()

class DataPipeline:
    def __init__(self):
        self.username = os.getenv('API_USERNAME')
        self.password = os.getenv('API_PASSWORD')
        self.base_url = os.getenv('API_BASE_URL')
        self.db = DatabaseConnection()
        
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
                return []  # Return empty list instead of None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            return []  # Return empty list instead of None
    
    def create_products_table(self):
        """Create products table schema based on actual API response"""
        schema = """
            id INT AUTO_INCREMENT PRIMARY KEY,
            uri VARCHAR(500),
            product_code VARCHAR(100) NOT NULL,
            allocated_qty INT DEFAULT 0,
            base_retail DECIMAL(10,2) DEFAULT 0.00,
            branch_code VARCHAR(50),
            brand VARCHAR(255),
            category VARCHAR(100),
            created_date VARCHAR(50),
            cross_reference_number JSON,
            description TEXT,
            discount JSON,
            group_name VARCHAR(255),
            linked_to JSON,
            oem_number VARCHAR(100),
            origin VARCHAR(10),
            popular_number_one VARCHAR(100),
            popular_number_two VARCHAR(100),
            popular_number_three VARCHAR(100),
            qoh INT DEFAULT 0,
            retail JSON,
            special_offer_id VARCHAR(100),
            special_price VARCHAR(50),
            type VARCHAR(10),
            u2version VARCHAR(100),
            unit_price JSON,
            uom VARCHAR(20),
            vat_category VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_product_code (product_code),
            INDEX idx_category (category),
            INDEX idx_branch_code (branch_code),
            INDEX idx_brand (brand)
        """
        self.db.create_table_if_not_exists('products', schema)
    
    def safe_decimal(self, value, default=0.00):
        """Safely convert value to decimal"""
        try:
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return Decimal(str(default))
            return Decimal(str(value))
        except (ValueError, TypeError, decimal.InvalidOperation):
            return Decimal(str(default))
    
    def safe_int(self, value, default=0):
        """Safely convert value to int"""
        try:
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return default
            return int(float(value))  # Handle decimal strings
        except (ValueError, TypeError):
            return default
    
    def insert_or_update_products(self, products):
        """Insert or update products in the database"""
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
                check_query = "SELECT id FROM products WHERE product_code = %s"
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
                        uri = %s, allocated_qty = %s, base_retail = %s, branch_code = %s,
                        brand = %s, category = %s, created_date = %s, cross_reference_number = %s,
                        description = %s, discount = %s, group_name = %s, linked_to = %s,
                        oem_number = %s, origin = %s, popular_number_one = %s, popular_number_two = %s,
                        popular_number_three = %s, qoh = %s, retail = %s, special_offer_id = %s,
                        special_price = %s, type = %s, u2version = %s, unit_price = %s,
                        uom = %s, vat_category = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE product_code = %s
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
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                             %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    params.insert(1, product_code)  # Insert product_code at position 1
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
        logging.info(f"Starting data pipeline for resource: {resource}")
        
        # Connect to database
        if not self.db.connect():
            logging.error("Failed to connect to database")
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
                    if consecutive_empty_pages >= 3:  # Stop after 3 consecutive empty pages
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
            
            logging.info(f"Pipeline completed. Total records processed: {total_records}")
            return True
            
        except Exception as e:
            logging.error(f"Pipeline failed: {e}")
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
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return None
        finally:
            self.db.disconnect()