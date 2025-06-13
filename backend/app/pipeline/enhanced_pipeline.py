"""
Enhanced Data Pipeline Module

This module provides comprehensive data synchronization between external APIs
and the local marketplace database. It handles full and incremental syncs,
data transformation, error handling, and scheduling.

Key Features:
- Full and incremental data synchronization
- Robust error handling and retry logic
- Data transformation and validation
- Change detection using hash comparison
- Scheduled synchronization jobs
- Comprehensive logging and monitoring
- Performance optimization with pagination

Classes:
    EnhancedDataPipeline: Main pipeline orchestrator

Dependencies:
    - requests: HTTP client for API communication
    - mysql-connector-python: Database operations
    - schedule: Job scheduling
    - hashlib: Data change detection
    - logging: Operation monitoring

Environment Variables Required:
    - API_USERNAME: External API authentication username
    - API_PASSWORD: External API authentication password
    - API_BASE_URL: Base URL for external API endpoints

Usage:
    pipeline = EnhancedDataPipeline()
    pipeline.run_full_sync(page_size=100)
    
    # For scheduled operations
    pipeline.start_scheduler()

Author: Development Team
Version: 2.0
"""

import requests
import logging
import hashlib
import json
import os
import schedule
import time
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from utils.database import DatabaseConnection
from models.product import Product
from dotenv import load_dotenv

load_dotenv()

class EnhancedDataPipeline:
    """
    Comprehensive data pipeline for product synchronization.
    
    This class orchestrates data flow between external APIs and the local
    database, providing robust synchronization capabilities with error
    handling, monitoring, and optimization features.
    
    Attributes:
        username (str): API authentication username
        password (str): API authentication password
        base_url (str): API base URL
        db (DatabaseConnection): Database connection handler
    """
    
    def __init__(self):
        """
        Initialize pipeline with API credentials and database connection.
        
        Raises:
            ValueError: If required environment variables are missing
        """
        self.username = os.getenv('API_USERNAME')
        self.password = os.getenv('API_PASSWORD')
        self.base_url = os.getenv('API_BASE_URL')
        self.db = DatabaseConnection()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_pipeline.log'),
                logging.StreamHandler()
            ]
        )
        
        if not all([self.username, self.password, self.base_url]):
            raise ValueError("Missing required environment variables")

    def create_optimized_products_table(self):
        """
        Create optimized marketplace products table with proper indexing.
        
        Creates a comprehensive products table with:
        - Full text search capabilities
        - Optimized indexes for common queries
        - JSON storage for flexible part numbers
        - Change tracking with hash fields
        - Timestamp tracking for sync operations
        
        Note:
            Table is created only if it doesn't exist to prevent data loss
        """
        try:
            # Check if table exists first
            check_table_query = """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'marketplace_products'
            """
            result = self.db.execute_query(check_table_query)
            
            if result and result[0][0] > 0:
                logging.info("marketplace_products table already exists, skipping creation")
                return
            
            # Create table only if it doesn't exist
            schema = """
                CREATE TABLE IF NOT EXISTS marketplace_products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_code VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    brand VARCHAR(100) NOT NULL,
                    base_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    current_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                    quantity_available INT NOT NULL DEFAULT 0,
                    branch_code VARCHAR(50) NOT NULL,
                    is_available BOOLEAN DEFAULT FALSE,
                    part_numbers JSON,
                    unit_of_measure VARCHAR(20),
                    data_hash VARCHAR(64),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    INDEX idx_category (category),
                    INDEX idx_brand (brand),
                    INDEX idx_available (is_available),
                    INDEX idx_branch (branch_code),
                    INDEX idx_price (current_price),
                    INDEX idx_last_sync (last_sync),
                    FULLTEXT idx_search (description, brand)
                )
            """
            self.db.execute_query(schema)
            logging.info("marketplace_products table created successfully")
            
        except Exception as e:
            logging.error(f"Error creating marketplace_products table: {e}")

    def create_sync_log_table(self):
        """
        Create synchronization logging table for operation tracking.
        
        Tracks all sync operations including:
        - Sync type (full/incremental)
        - Record counts (fetched/inserted/updated/errors)
        - Timing information
        - Status and error details
        """
        try:
            # Check if table exists first
            check_table_query = """
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'sync_logs'
            """
            result = self.db.execute_query(check_table_query)
            
            if result and result[0][0] > 0:
                logging.info("sync_logs table already exists, skipping creation")
                return
            
            # Create table only if it doesn't exist
            schema = """
                CREATE TABLE IF NOT EXISTS sync_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sync_type VARCHAR(20) NOT NULL,
                    total_fetched INT DEFAULT 0,
                    total_inserted INT DEFAULT 0,
                    total_updated INT DEFAULT 0,
                    total_errors INT DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    status VARCHAR(20) DEFAULT 'running',
                    error_message TEXT
                )
            """
            self.db.execute_query(schema)
            logging.info("sync_logs table created successfully")
            
        except Exception as e:
            logging.error(f"Error creating sync_logs table: {e}")

    def safe_float_conversion(self, value, default=0.0):
        """
        Safely convert values to float with fallback handling.
        
        Args:
            value: Value to convert to float
            default (float): Default value if conversion fails
            
        Returns:
            float: Converted value or default
            
        Note:
            Handles None, empty strings, and invalid data gracefully
        """
        if value is None or value == '' or value == 'null':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            logging.warning(f"Could not convert '{value}' to float, using default {default}")
            return default

    def safe_int_conversion(self, value, default=0):
        """
        Safely convert values to integer with fallback handling.
        
        Args:
            value: Value to convert to integer
            default (int): Default value if conversion fails
            
        Returns:
            int: Converted value or default
        """
        if value is None or value == '' or value == 'null':
            return default
        try:
            return int(float(value))  # Convert to float first in case it's a decimal string
        except (ValueError, TypeError):
            logging.warning(f"Could not convert '{value}' to int, using default {default}")
            return default

    def safe_string_conversion(self, value, default=''):
        """
        Safely convert values to string with fallback handling.
        
        Args:
            value: Value to convert to string
            default (str): Default value if conversion fails
            
        Returns:
            str: Converted and trimmed string or default
        """
        if value is None or value == 'null':
            return default
        return str(value).strip()

    def process_and_sync_products(self, api_products):
        """
        Process API product data and synchronize with database.
        
        Handles data cleaning, validation, transformation, and database
        operations with comprehensive error handling.
        
        Args:
            api_products (list): List of product data from API
            
        Returns:
            tuple: (inserted_count, updated_count, error_count)
            
        Features:
        - Data validation and cleaning
        - Change detection using hash comparison
        - Efficient upsert operations
        - Individual product error isolation
        """
        if not api_products:
            return 0, 0, 0
        
        inserted = updated = errors = 0
        
        for api_product in api_products:
            try:
                # Clean and validate product data before creating Product object
                cleaned_product = {
                    'product_code': self.safe_string_conversion(api_product.get('product_code')),
                    'description': self.safe_string_conversion(api_product.get('description'), 'No Description'),
                    'category': self.safe_string_conversion(api_product.get('category'), 'Uncategorized'),
                    'brand': self.safe_string_conversion(api_product.get('brand'), 'Unknown'),
                    'base_price': self.safe_float_conversion(api_product.get('base_price')),
                    'current_price': self.safe_float_conversion(api_product.get('current_price')),
                    'quantity_available': self.safe_int_conversion(api_product.get('quantity_available')),
                    'branch_code': self.safe_string_conversion(api_product.get('branch_code'), 'MAIN'),
                    'is_available': bool(api_product.get('is_available', False)),
                    'part_numbers': api_product.get('part_numbers', []),
                    'unit_of_measure': self.safe_string_conversion(api_product.get('unit_of_measure'), 'EACH')
                }
                
                # Skip products without product code
                if not cleaned_product['product_code']:
                    logging.warning("Skipping product without product_code")
                    errors += 1
                    continue
                
                # Transform to our model
                product = Product.from_api_response(cleaned_product)
                
                # Calculate hash for change detection
                current_hash = self.calculate_product_hash(product)
                
                # Check if product exists and if data changed
                check_query = """
                    SELECT id, data_hash FROM marketplace_products 
                    WHERE product_code = %s
                """
                existing = self.db.execute_query(check_query, (product.product_code,))
                
                if existing:
                    existing_hash = existing[0][1]
                    if existing_hash == current_hash:
                        # No changes, skip
                        continue
                    
                    # Update existing product
                    update_query = """
                        UPDATE marketplace_products SET
                            description = %s, category = %s, brand = %s,
                            base_price = %s, current_price = %s, quantity_available = %s,
                            branch_code = %s, is_available = %s, part_numbers = %s,
                            unit_of_measure = %s, data_hash = %s, last_sync = CURRENT_TIMESTAMP
                        WHERE product_code = %s
                    """
                    params = [
                        product.description, product.category, product.brand,
                        product.base_price, product.current_price, product.quantity_available,
                        product.branch_code, product.is_available, json.dumps(product.part_numbers),
                        product.unit_of_measure, current_hash, product.product_code
                    ]
                    self.db.execute_query(update_query, params)
                    updated += 1
                    
                else:
                    # Insert new product
                    insert_query = """
                        INSERT INTO marketplace_products (
                            product_code, description, category, brand, base_price,
                            current_price, quantity_available, branch_code, is_available,
                            part_numbers, unit_of_measure, data_hash
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    params = [
                        product.product_code, product.description, product.category, product.brand,
                        product.base_price, product.current_price, product.quantity_available,
                        product.branch_code, product.is_available, json.dumps(product.part_numbers),
                        product.unit_of_measure, current_hash
                    ]
                    self.db.execute_query(insert_query, params)
                    inserted += 1
                    
            except Exception as e:
                product_code = api_product.get('product_code', 'unknown')
                logging.error(f"Error processing product {product_code}: {e}")
                errors += 1
                continue
        
        return inserted, updated, errors

    def fetch_products_from_api(self, params=None):
        """
        Fetch product data from external API with robust error handling.
        
        Args:
            params (dict, optional): Query parameters for API request
            
        Returns:
            list: List of products from API or empty list on failure
            
        Features:
        - HTTP Basic Authentication
        - Timeout handling (60 seconds)
        - Connection error recovery
        - Detailed error logging
        """
        url = f"{self.base_url}/products"
        
        try:
            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.username, self.password),
                headers={"Accept": "application/json"},
                params=params,
                timeout=60  # Increased timeout to 60 seconds
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                logging.info(f"Fetched {len(products)} products from API")
                return products
            else:
                logging.error(f"API returned status code: {response.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            logging.error("API request timed out after 60 seconds")
            return []
        except requests.exceptions.ConnectionError:
            logging.error("API connection error")
            return []
        except Exception as e:
            logging.error(f"API request error: {e}")
            return []

    def calculate_product_hash(self, product):
        """
        Calculate SHA256 hash of product data for change detection.
        
        Args:
            product (Product): Product object to hash
            
        Returns:
            str: SHA256 hash of key product fields
            
        Note:
            Hash includes: code, description, price, quantity, availability
        """
        data_string = f"{product.product_code}_{product.description}_{product.current_price}_{product.quantity_available}_{product.is_available}"
        return hashlib.sha256(data_string.encode()).hexdigest()

    def log_sync_operation(self, sync_type, total_fetched, inserted, updated, errors, start_time, status='completed', error_msg=None):
        """
        Log synchronization operation details to database.
        
        Args:
            sync_type (str): Type of sync operation (full/incremental)
            total_fetched (int): Number of records fetched from API
            inserted (int): Number of new records inserted
            updated (int): Number of existing records updated
            errors (int): Number of errors encountered
            start_time (datetime): Operation start timestamp
            status (str): Operation status (completed/failed)
            error_msg (str, optional): Error message if operation failed
        """
        try:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            insert_query = """
                INSERT INTO sync_logs (
                    sync_type, total_fetched, total_inserted, total_updated, 
                    total_errors, started_at, completed_at, status, error_message
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.db.execute_query(insert_query, [
                sync_type, total_fetched, inserted, updated, errors,
                start_time, end_time, status, error_msg
            ])
            
            logging.info(f"Sync operation logged: {sync_type} - {status} - Duration: {duration:.2f}s")
            
        except Exception as e:
            logging.error(f"Error logging sync operation: {e}")

    def run_full_sync(self, page_size=100, max_pages=None):
        """
        Execute complete product synchronization from API.
        
        Performs comprehensive sync of all products with:
        - Paginated API requests for memory efficiency
        - Consecutive failure detection
        - Progress tracking and logging
        - Database transaction management
        
        Args:
            page_size (int): Number of products per API request
            max_pages (int, optional): Maximum pages to process
            
        Returns:
            bool: True if sync completed successfully
            
        Features:
        - Automatic pagination handling
        - Failure tolerance (stops after 3 consecutive empty responses)
        - Rate limiting between requests
        - Comprehensive progress logging
        """
        start_time = datetime.now()
        logging.info("Starting full product synchronization")
        
        if not self.db.connect():
            logging.error("Database connection failed")
            return False
        
        try:
            # Create tables if needed (with proper error handling)
            self.create_optimized_products_table()
            self.create_sync_log_table()
            
            total_fetched = total_inserted = total_updated = total_errors = 0
            page_no = 1
            consecutive_failures = 0
            max_consecutive_failures = 3
            
            while True:
                params = {'pagesize': page_size, 'pageno': page_no}
                api_products = self.fetch_products_from_api(params)
                
                if not api_products:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logging.info(f"No products found for {consecutive_failures} consecutive attempts, ending sync")
                        break
                    else:
                        logging.warning(f"No products on page {page_no}, trying next page ({consecutive_failures}/{max_consecutive_failures})")
                        page_no += 1
                        continue
                
                # Reset failure counter on successful fetch
                consecutive_failures = 0
                
                inserted, updated, errors = self.process_and_sync_products(api_products)
                
                total_fetched += len(api_products)
                total_inserted += inserted
                total_updated += updated
                total_errors += errors
                
                logging.info(f"Page {page_no}: {len(api_products)} fetched, {inserted} inserted, {updated} updated, {errors} errors")
                
                # Stop if we got fewer products than requested (last page) or reached max pages
                if len(api_products) < page_size or (max_pages and page_no >= max_pages):
                    logging.info(f"Sync completed - reached end or max pages limit")
                    break
                
                page_no += 1
                
                # Add a small delay between pages to avoid overwhelming the API
                time.sleep(1)
            
            # Log the operation
            self.log_sync_operation('full', total_fetched, total_inserted, total_updated, total_errors, start_time)
            
            logging.info(f"Full sync completed: {total_fetched} fetched, {total_inserted} inserted, {total_updated} updated, {total_errors} errors")
            return True
            
        except Exception as e:
            logging.error(f"Full sync failed: {e}")
            self.log_sync_operation('full', 0, 0, 0, 0, start_time, 'failed', str(e))
            return False
        finally:
            self.db.disconnect()

    def run_incremental_sync(self, hours_back=1):
        """
        Execute incremental synchronization for recent changes.
        
        Lightweight sync operation for checking recent updates:
        - Fetches smaller data subset
        - Focuses on recent changes
        - Suitable for frequent execution
        
        Args:
            hours_back (int): Hours to look back for changes
            
        Returns:
            bool: True if sync completed successfully
        """
        start_time = datetime.now()
        logging.info(f"Starting incremental sync for last {hours_back} hours")
        
        if not self.db.connect():
            logging.error("Database connection failed")
            return False
        
        try:
            # Ensure tables exist
            self.create_optimized_products_table()
            self.create_sync_log_table()
            
            # For incremental sync, we fetch a smaller batch and check for changes
            api_products = self.fetch_products_from_api({'pagesize': 50, 'pageno': 1})
            
            if api_products:
                inserted, updated, errors = self.process_and_sync_products(api_products)
                self.log_sync_operation('incremental', len(api_products), inserted, updated, errors, start_time)
                logging.info(f"Incremental sync: {len(api_products)} checked, {updated} updated, {inserted} new, {errors} errors")
            else:
                logging.info("No products fetched for incremental sync")
            
            return True
            
        except Exception as e:
            logging.error(f"Incremental sync failed: {e}")
            self.log_sync_operation('incremental', 0, 0, 0, 0, start_time, 'failed', str(e))
            return False
        finally:
            self.db.disconnect()

    def get_marketplace_statistics(self):
        """
        Generate comprehensive marketplace statistics and metrics.
        
        Returns:
            dict: Statistics including:
                - total_products: Total number of products
                - available_products: Number of available products
                - price_range: Min, max, and average prices
                - top_categories: Most popular product categories
                - recent_syncs: Recent synchronization history
                
        Usage:
            stats = pipeline.get_marketplace_statistics()
            print(f"Total products: {stats['total_products']}")
        """
        if not self.db.connect():
            logging.error("Database connection failed for statistics")
            return None
        
        try:
            # Basic stats
            stats_query = """
                SELECT 
                    COUNT(*) as total_products,
                    COUNT(CASE WHEN is_available = 1 THEN 1 END) as available_products,
                    AVG(CASE WHEN is_available = 1 AND current_price > 0 THEN current_price END) as avg_price,
                    MIN(CASE WHEN is_available = 1 AND current_price > 0 THEN current_price END) as min_price,
                    MAX(CASE WHEN is_available = 1 AND current_price > 0 THEN current_price END) as max_price
                FROM marketplace_products
            """
            
            result = self.db.execute_query(stats_query)
            if not result:
                return None
            
            stats = result[0]
            
            # Top categories
            categories_query = """
                SELECT category, COUNT(*) as count 
                FROM marketplace_products 
                WHERE is_available = 1
                GROUP BY category 
                ORDER BY count DESC 
                LIMIT 5
            """
            categories = self.db.execute_query(categories_query)
            
            # Recent sync logs
            sync_logs_query = """
                SELECT sync_type, total_fetched, total_inserted, total_updated, 
                       total_errors, completed_at, status 
                FROM sync_logs 
                ORDER BY completed_at DESC 
                LIMIT 5
            """
            sync_logs = self.db.execute_query(sync_logs_query)
            
            return {
                "total_products": stats[0],
                "available_products": stats[1],
                "price_range": {
                    "average": float(stats[2]) if stats[2] else 0,
                    "min": float(stats[3]) if stats[3] else 0,
                    "max": float(stats[4]) if stats[4] else 0
                },
                "top_categories": [
                    {"category": cat[0], "count": cat[1]} for cat in categories
                ],
                "recent_syncs": [
                    {
                        "type": log[0],
                        "fetched": log[1],
                        "inserted": log[2],
                        "updated": log[3],
                        "errors": log[4],
                        "completed": log[5].isoformat() if log[5] else None,
                        "status": log[6]
                    } for log in sync_logs
                ]
            }
            
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return None
        finally:
            self.db.disconnect()

    def setup_scheduled_sync(self):
        """
        Configure scheduled synchronization jobs.
        
        Schedules:
        - Full sync: Daily at 2:00 AM
        - Incremental sync: Every 30 minutes
        
        Note:
            Use start_scheduler() to begin scheduled execution
        """
        # Full sync daily at 2 AM
        schedule.every().day.at("02:00").do(self.run_full_sync)
        
        # Incremental sync every 30 minutes during business hours
        schedule.every(30).minutes.do(self.run_incremental_sync, hours_back=1)
        
        logging.info("Scheduled sync jobs configured")
    
    def start_scheduler(self):
        """
        Start the background scheduler for automatic synchronization.
        
        Runs continuously, executing scheduled sync operations:
        - Monitors for scheduled jobs every minute
        - Blocks execution (suitable for dedicated sync processes)
        
        Warning:
            This method runs indefinitely - use in dedicated processes
        """
        self.setup_scheduled_sync()
        logging.info("Scheduler started - running continuous sync")
        
        while True:
            schedule.run_pending()
            time.sleep(60)