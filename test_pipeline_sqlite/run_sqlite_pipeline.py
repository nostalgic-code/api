#!/usr/bin/env python3
from test_pipeline_sqlite.data_pipeline_sqlite import DataPipelineSQLite
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='SQLite Data Pipeline Runner')
    parser.add_argument('--db-path', default='pipeline_data.db',
                       help='SQLite database file path (default: pipeline_data.db)')
    parser.add_argument('--resource', default='products',
                       help='Resource to fetch (default: products)')
    parser.add_argument('--page-size', type=int, default=100,
                       help='Page size for API calls (default: 100)')
    parser.add_argument('--max-pages', type=int,
                       help='Maximum pages to fetch (default: all)')
    parser.add_argument('--show-stats', action='store_true',
                       help='Show database statistics after pipeline')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting SQLite Pipeline")
    print(f"📁 Database: {args.db_path}")
    print(f"📦 Resource: {args.resource}")
    print(f"📄 Page size: {args.page_size}")
    print(f"📊 Max pages: {args.max_pages or 'All'}")
    print("-" * 50)
    
    try:
        # Initialize pipeline
        pipeline = DataPipelineSQLite(args.db_path)
        
        # Run pipeline
        success = pipeline.run_pipeline(
            resource=args.resource,
            page_size=args.page_size,
            max_pages=args.max_pages
        )
        
        if success:
            print("\n✅ Pipeline completed successfully!")
            
            if args.show_stats:
                print("\n📊 Database Statistics:")
                stats = pipeline.get_product_statistics()
                if stats:
                    print(f"  📦 Total products: {stats.get('total_products', 0)}")
                    print(f"  💾 Database size: {stats.get('database_size_mb', 0)} MB")
                    print(f"  🏷️  Top categories: {len(stats.get('top_categories', []))}")
                    print(f"  🏢 Branches: {len(stats.get('branches', []))}")
            
            sys.exit(0)
        else:
            print("\n❌ Pipeline failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Pipeline error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()