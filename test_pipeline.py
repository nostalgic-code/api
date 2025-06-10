#!/usr/bin/env python3
import os
import sys
from data_pipeline import DataPipeline
from database import DatabaseConnection

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    db = DatabaseConnection()
    if db.connect():
        print("✅ Database connection successful")
        db.disconnect()
        return True
    else:
        print("❌ Database connection failed")
        return False

def test_api_connection():
    """Test API connection"""
    print("Testing API connection...")
    pipeline = DataPipeline()
    products = pipeline.fetch_data_from_api('products', {'pagesize': 1, 'pageno': 1})
    if products:
        print(f"✅ API connection successful - fetched {len(products)} products")
        return True
    else:
        print("❌ API connection failed")
        return False

def test_full_pipeline():
    """Test full pipeline with limited data"""
    print("Testing full pipeline...")
    pipeline = DataPipeline()
    success = pipeline.run_pipeline(resource='products', page_size=10, max_pages=1)
    if success:
        print("✅ Pipeline test successful")
        return True
    else:
        print("❌ Pipeline test failed")
        return False

if __name__ == "__main__":
    print("Running pipeline tests...\n")
    
    tests = [
        test_database_connection,
        test_api_connection,
        test_full_pipeline
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Tests passed: {passed}/{len(tests)}")
    if passed == len(tests):
        print("🎉 All tests passed! Your pipeline is ready to use.")
    else:
        print("❌ Some tests failed. Please check your configuration.")