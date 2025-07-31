#!/usr/bin/env python3
import os
import sys
from backend.application.utils.database_sqlite import SQLiteConnection
from test_pipeline_sqlite.data_pipeline_sqlite import DataPipelineSQLite
from dotenv import load_dotenv

load_dotenv()

def test_environment_variables():
    """Test that all required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = ['API_USERNAME', 'API_PASSWORD', 'API_BASE_URL']
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            # Mask password for security
            display_value = value if var != 'API_PASSWORD' else '*' * len(value)
            print(f"  ✅ {var}: {display_value}")
    
    if missing:
        print(f"  ❌ Missing variables: {', '.join(missing)}")
        return False
    
    print("  ✅ All environment variables are set\n")
    return True

def test_sqlite_connection():
    """Test SQLite database connection"""
    print("🔗 Testing SQLite database connection...")
    
    try:
        db = SQLiteConnection('test_pipeline.db')
        result = db.test_connection()
        
        if result['connected']:
            print("  ✅ Connection successful!")
            print(f"  📊 Database: {result.get('database', 'Unknown')}")
            print(f"  🏷️  SQLite Version: {result.get('sqlite_version', 'Unknown')}")
            print(f"  📁 DB Size: {result.get('db_size_bytes', 0)} bytes")
            print(f"  🔧 Can create tables: {'Yes' if result.get('can_create_tables') else 'No'}")
            return True
        else:
            print(f"  ❌ Connection failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"  ❌ Connection test failed: {e}")
        return False

def test_api_connection():
    """Test API connection"""
    print("🌐 Testing API connection...")
    
    try:
        pipeline = DataPipelineSQLite('test_pipeline.db')
        products = pipeline.fetch_data_from_api('products', {'pagesize': 1, 'pageno': 1})
        if products:
            print(f"  ✅ API connection successful - fetched {len(products)} products")
            print(f"  📦 Sample product: {products[0].get('product_code', 'N/A')}")
            return True
        else:
            print("  ❌ API connection failed or no products returned")
            return False
            
    except Exception as e:
        print(f"  ❌ API test failed: {e}")
        return False

def test_table_operations():
    """Test table creation and basic operations"""
    print("🏗️  Testing table operations...")
    
    try:
        db = SQLiteConnection('test_pipeline.db')
        
        if not db.connect():
            print("  ❌ Could not connect to database")
            return False
        
        # Test table creation
        test_schema = """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_field TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        """
        
        db.create_table_if_not_exists('test_pipeline_table', test_schema)
        print("  ✅ Table creation successful")
        
        # Test insert
        insert_query = "INSERT INTO test_pipeline_table (test_field) VALUES (?)"
        db.execute_query(insert_query, ('test_value',))
        print("  ✅ Insert operation successful")
        
        # Test select
        select_query = "SELECT * FROM test_pipeline_table WHERE test_field = ?"
        result = db.execute_query(select_query, ('test_value',))
        print(f"  ✅ Select operation successful - Found {len(result)} record(s)")
        
        # Clean up
        db.execute_query("DROP TABLE test_pipeline_table")
        print("  ✅ Cleanup successful")
        
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"  ❌ Table operations failed: {e}")
        return False

def test_mini_pipeline():
    """Test a mini pipeline run"""
    print("🚀 Testing mini pipeline...")
    
    try:
        pipeline = DataPipelineSQLite('test_pipeline.db')
        success = pipeline.run_pipeline(resource='products', page_size=5, max_pages=1)
        
        if success:
            print("  ✅ Mini pipeline successful")
            
            # Get statistics
            stats = pipeline.get_product_statistics()
            if stats:
                print(f"  📊 Total products in DB: {stats.get('total_products', 0)}")
                print(f"  💾 Database size: {stats.get('database_size_mb', 0)} MB")
            
            return True
        else:
            print("  ❌ Mini pipeline failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Pipeline test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SQLite Database Pipeline Test Suite\n")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("SQLite Connection", test_sqlite_connection),
        ("API Connection", test_api_connection),
        ("Table Operations", test_table_operations),
        ("Mini Pipeline", test_mini_pipeline)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test PASSED")
        else:
            print(f"❌ {test_name} test FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your SQLite pipeline is working correctly.")
        print(f"📁 Database file: test_pipeline.db")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check your configuration.")
        sys.exit(1)