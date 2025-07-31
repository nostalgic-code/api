#!/usr/bin/env python3
import os
import sys
from backend.application.utils.database import DatabaseConnection
from dotenv import load_dotenv

load_dotenv()

def test_environment_variables():
    """Test that all required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            # Mask password for security
            display_value = value if var != 'DB_PASSWORD' else '*' * len(value)
            print(f"  ✅ {var}: {display_value}")
    
    if missing:
        print(f"  ❌ Missing variables: {', '.join(missing)}")
        return False
    
    print("  ✅ All environment variables are set\n")
    return True

def test_basic_connection():
    """Test basic database connection"""
    print("🔗 Testing basic database connection...")
    
    try:
        db = DatabaseConnection()
        result = db.test_connection()
        
        if result['connected']:
            print("  ✅ Connection successful!")
            print(f"  📊 Database: {result.get('database', 'Unknown')}")
            print(f"  👤 User: {result.get('user', 'Unknown')}")
            print(f"  🏷️  MySQL Version: {result.get('mysql_version', 'Unknown')}")
            print(f"  🔧 Can create tables: {'Yes' if result.get('can_create_tables') else 'No'}")
            return True
        else:
            print(f"  ❌ Connection failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"  ❌ Connection test failed: {e}")
        return False

def test_table_operations():
    """Test table creation and basic operations"""
    print("\n🏗️  Testing table operations...")
    
    try:
        db = DatabaseConnection()
        
        if not db.connect():
            print("  ❌ Could not connect to database")
            return False
        
        # Test table creation
        test_schema = """
            id INT AUTO_INCREMENT PRIMARY KEY,
            test_field VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
        
        db.create_table_if_not_exists('test_pipeline_table', test_schema)
        print("  ✅ Table creation successful")
        
        # Test insert
        insert_query = "INSERT INTO test_pipeline_table (test_field) VALUES (%s)"
        db.execute_query(insert_query, ('test_value',))
        print("  ✅ Insert operation successful")
        
        # Test select
        select_query = "SELECT * FROM test_pipeline_table WHERE test_field = %s"
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

if __name__ == "__main__":
    print("🚀 Database Connection Test Suite\n")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Basic Connection", test_basic_connection),
        ("Table Operations", test_table_operations)
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
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your database connection is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check your database configuration.")
        sys.exit(1)