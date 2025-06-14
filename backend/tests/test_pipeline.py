#!/usr/bin/env python3
"""
Test script to run the enhanced pipeline with limited data
"""
from backend.pipeline.enhanced_pipeline import EnhancedDataPipeline
import logging
import sys

def test_pipeline():
    """Test the pipeline with 5 pages of 20 items each"""
    
    # Configure logging to see what's happening
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("TESTING ENHANCED PIPELINE")
    print("=" * 60)
    print("Target: 5 pages × 20 items = 100 products maximum")
    print("-" * 60)
    
    try:
        # Initialize pipeline
        print("1. Initializing pipeline...")
        pipeline = EnhancedDataPipeline()
        print("✅ Pipeline initialized successfully")
        
        # Test database connection
        print("\n2. Testing database connection...")
        if not pipeline.db.connect():
            print("❌ Database connection failed")
            return False
        print("✅ Database connected successfully")
        pipeline.db.disconnect()
        
        # Run limited sync
        print("\n3. Starting limited sync (5 pages × 20 items)...")
        print("This may take a few minutes...")
        
        success = pipeline.run_full_sync(
            page_size=20,      # 20 items per page
            max_pages=5        # Maximum 5 pages
        )
        
        if success:
            print("\n✅ Pipeline test completed successfully!")
            
            # Get and display statistics
            print("\n4. Getting marketplace statistics...")
            stats = pipeline.get_marketplace_statistics()
            
            if stats:
                print("\n📊 MARKETPLACE STATISTICS:")
                print("-" * 40)
                print(f"Total products in database: {stats.get('total_products', 0)}")
                print(f"Available products: {stats.get('available_products', 0)}")
                
                price_range = stats.get('price_range')
                if price_range:
                    print(f"Price range: R{price_range['min']:.2f} - R{price_range['max']:.2f}")
                    print(f"Average price: R{price_range['average']:.2f}")
                
                top_categories = stats.get('top_categories', [])
                if top_categories:
                    print("\nTop 5 categories:")
                    for i, cat in enumerate(top_categories[:5], 1):
                        print(f"  {i}. {cat['category']}: {cat['count']} products")
                
                recent_syncs = stats.get('recent_syncs', [])
                if recent_syncs:
                    latest_sync = recent_syncs[0]
                    print(f"\nLatest sync: {latest_sync['type']} - {latest_sync['status']}")
                    print(f"Inserted: {latest_sync['inserted']}, Updated: {latest_sync['updated']}")
            
            print("\n🎉 TEST COMPLETED SUCCESSFULLY!")
            print("\nNext steps:")
            print("- Check your database for the 'marketplace_products' table")
            print("- Test the Flask API endpoints")
            print("- Run a full sync when ready")
            
            return True
            
        else:
            print("\n❌ Pipeline test failed!")
            return False
            
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("\nPlease check your .env file contains:")
        print("- API_USERNAME")
        print("- API_PASSWORD") 
        print("- API_BASE_URL")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("Checking prerequisites...")
    
    # Check if required modules exist
    try:
        from backend.application.utils.database import DatabaseConnection
        print("✅ database.py found")
    except ImportError:
        print("❌ database.py not found")
        return False
    
    try:
        from models.product import Product
        print("✅ product_model.py found")
    except ImportError:
        print("❌ models/product_model.py not found")
        return False
    
    # Check environment variables
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['API_USERNAME', 'API_PASSWORD', 'API_BASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All environment variables found")
    return True

if __name__ == "__main__":
    print("ENHANCED PIPELINE TEST")
    print("=" * 60)
    
    # Check prerequisites first
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        sys.exit(1)
    
    print("✅ Prerequisites check passed\n")
    
    # Run the test
    success = test_pipeline()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)