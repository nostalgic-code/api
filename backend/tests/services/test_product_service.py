service_test_content = '''"""
Product Service Test Suite

Comprehensive test suite for the ProductService class.
Tests all service methods with various scenarios including success cases,
error handling, edge cases, database interactions, and validation.

Test Coverage:
- get_products() with filters and pagination
- get_product_by_code()
- search_products()
- get_products_by_category()
- get_products_by_brand()
- get_product_statistics()
- validate_product_data()
- get_categories()
- get_brands()

Dependencies:
    - pytest
    - Mock database connections
    - Test fixtures and sample data

Usage:
    pytest test_product_service.py -v

Author: Development Team
Version: 1.0
"""'''

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from backend.application.services.product_service import ProductService


class TestProductService:
    """Test suite for ProductService class"""
    
    @pytest.fixture
    def service(self):
        """Create ProductService instance for testing"""
        return ProductService()
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        with patch('backend.application.services.product_service.DatabaseConnection') as mock_db_class:
            mock_db = Mock()
            mock_db.connect.return_value = True
            mock_db.execute_query.return_value = []
            mock_db.disconnect.return_value = None
            mock_db_class.return_value = mock_db
            yield mock_db
    
    @pytest.fixture
    def sample_db_rows(self):
        """Sample database rows for testing"""
        return [
            ('PROD001', 'Test Product 1', 'Electronics', 'TestBrand', 99.99, 10, 'EA', '["PN001","PN002"]', True),
            ('PROD002', 'Test Product 2', 'Tools', 'AnotherBrand', 149.99, 5, 'EA', '["PN003"]', True),
            ('PROD003', 'Test Product 3', 'Hardware', 'ThirdBrand', 75.50, 0, 'EA', '[]', False)
        ]
    
    @pytest.fixture
    def sample_products(self):
        """Sample formatted product data"""
        return [
            {
                "product_code": "PROD001",
                "description": "Test Product 1",
                "category": "Electronics",
                "brand": "TestBrand",
                "price": 99.99,
                "quantity_available": 10,
                "unit_of_measure": "EA",
                "part_numbers": ["PN001", "PN002"],
                "is_available": True
            },
            {
                "product_code": "PROD002",
                "description": "Test Product 2", 
                "category": "Tools",
                "brand": "AnotherBrand",
                "price": 149.99,
                "quantity_available": 5,
                "unit_of_measure": "EA",
                "part_numbers": ["PN003"],
                "is_available": True
            }
        ]

    # Test _format_product method
    def test_format_product_complete_data(self, service):
        """Test product formatting with complete data"""
        row = ('PROD001', 'Test Product', 'Electronics', 'TestBrand', 99.99, 10, 'EA', '["PN001"]', True)
        
        result = service._format_product(row)
        
        assert result['product_code'] == 'PROD001'
        assert result['description'] == 'Test Product'
        assert result['category'] == 'Electronics'
        assert result['brand'] == 'TestBrand'
        assert result['price'] == 99.99
        assert result['quantity_available'] == 10
        assert result['unit_of_measure'] == 'EA'
        assert result['part_numbers'] == '["PN001"]'
        assert result['is_available'] == True
    
    def test_format_product_minimal_data(self, service):
        """Test product formatting with minimal data"""
        row = ('PROD001', 'Test Product', 'Electronics', 'TestBrand', None, None, 'EA', None)
        
        result = service._format_product(row)
        
        assert result['product_code'] == 'PROD001'
        assert result['price'] == 0.0
        assert result['quantity_available'] == 0
        assert result['part_numbers'] == []
        assert result['is_available'] == True  # Default when not provided

    # Test get_products method
    def test_get_products_success_no_filters(self, service, mock_db, sample_db_rows):
        """Test get_products without filters"""
        # Mock count query
        mock_db.execute_query.side_effect = [
            [(3,)],  # Count result
            sample_db_rows  # Products result
        ]
        
        result = service.get_products()
        
        assert 'products' in result
        assert 'pagination' in result
        assert len(result['products']) == 3
        assert result['pagination']['total_items'] == 3
        assert result['pagination']['current_page'] == 1
        assert result['pagination']['items_per_page'] == 20
        
        # Verify database calls
        assert mock_db.execute_query.call_count == 2
        mock_db.connect.assert_called_once()
        mock_db.disconnect.assert_called_once()
    
    def test_get_products_with_filters(self, service, mock_db, sample_db_rows):
        """Test get_products with various filters"""
        mock_db.execute_query.side_effect = [
            [(2,)],  # Count result
            sample_db_rows[:2]  # Filtered products
        ]
        
        filters = {
            "available_only": True,
            "category": "Electronics",
            "brand": "TestBrand",
            "min_price": 50.0,
            "max_price": 200.0,
            "search": "test"
        }
        
        result = service.get_products(filters=filters)
        
        assert len(result['products']) == 2
        assert result['filters_applied'] == filters
        
        # Verify SQL query construction with filters
        calls = mock_db.execute_query.call_args_list
        count_call = calls[0]
        products_call = calls[1]
        
        # Check that WHERE conditions were added
        assert 'is_available = TRUE' in count_call[0][0]
        assert 'category = %s' in count_call[0][0]
        assert 'brand = %s' in count_call[0][0]
        assert 'current_price >= %s' in count_call[0][0]
        assert 'current_price <= %s' in count_call[0][0]
        assert 'LIKE %s' in count_call[0][0]
    
    def test_get_products_with_pagination(self, service, mock_db, sample_db_rows):
        """Test get_products with custom pagination"""
        mock_db.execute_query.side_effect = [
            [(10,)],  # Count result
            sample_db_rows[:2]  # Page 2 results
        ]
        
        pagination = {"page": 2, "limit": 5}
        
        result = service.get_products(pagination=pagination)
        
        assert result['pagination']['current_page'] == 2
        assert result['pagination']['items_per_page'] == 5
        assert result['pagination']['total_pages'] == 2  # 10 items / 5 per page
        
        # Verify LIMIT and OFFSET in query
        products_call = mock_db.execute_query.call_args_list[1]
        assert 'LIMIT %s OFFSET %s' in products_call[0][0]
        # Offset should be (page-1) * limit = (2-1) * 5 = 5
        assert 5 in products_call[0][1]  # OFFSET value
        assert 5 in products_call[0][1]  # LIMIT value
    
    def test_get_products_database_error(self, service, mock_db):
        """Test get_products when database raises exception"""
        mock_db.execute_query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception) as exc_info:
            service.get_products()
        
        assert "Database connection failed" in str(exc_info.value)
    
    def test_get_products_connection_failure(self, service):
        """Test get_products when database connection fails"""
        with patch('backend.application.services.product_service.DatabaseConnection') as mock_db_class:
            mock_db = Mock()
            mock_db.connect.return_value = False
            mock_db_class.return_value = mock_db
            
            with pytest.raises(Exception) as exc_info:
                service.get_products()
            
            assert "Database connection failed" in str(exc_info.value)

    # Test get_product_by_code method
    def test_get_product_by_code_success(self, service, mock_db, sample_db_rows):
        """Test successful product retrieval by code"""
        mock_db.execute_query.return_value = [sample_db_rows[0]]
        
        result = service.get_product_by_code('PROD001')
        
        assert result is not None
        assert result['product_code'] == 'PROD001'
        assert result['description'] == 'Test Product 1'
        
        # Verify query parameters
        call_args = mock_db.execute_query.call_args
        assert 'product_code = %s' in call_args[0][0]
        assert call_args[0][1] == ['PROD001']
    
    def test_get_product_by_code_not_found(self, service, mock_db):
        """Test product retrieval when product doesn't exist"""
        mock_db.execute_query.return_value = []
        
        result = service.get_product_by_code('NONEXISTENT')
        
        assert result is None
    
    def test_get_product_by_code_empty_code(self, service, mock_db):
        """Test product retrieval with empty product code"""
        with pytest.raises(ValueError) as exc_info:
            service.get_product_by_code('')
        
        assert "Product code is required" in str(exc_info.value)
    
    def test_get_product_by_code_whitespace_code(self, service, mock_db):
        """Test product retrieval with whitespace-only product code"""
        with pytest.raises(ValueError) as exc_info:
            service.get_product_by_code('   ')
        
        assert "Product code is required" in str(exc_info.value)
    
    def test_get_product_by_code_database_error(self, service, mock_db):
        """Test product retrieval when database raises exception"""
        mock_db.execute_query.side_effect = Exception("Query timeout")
        
        with pytest.raises(Exception) as exc_info:
            service.get_product_by_code('PROD001')
        
        assert "Query timeout" in str(exc_info.value)

    # Test search_products method
    def test_search_products_success(self, service, mock_db, sample_db_rows):
        """Test successful product search"""
        mock_db.execute_query.return_value = sample_db_rows[:2]
        
        result = service.search_products('test query')
        
        assert 'products' in result
        assert 'count' in result
        assert 'query' in result
        assert len(result['products']) == 2
        assert result['query'] == 'test query'
        assert result['count'] == 2
        
        # Verify search query construction
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        # Should search in multiple fields
        assert 'description LIKE %s' in query
        assert 'brand LIKE %s' in query
        assert 'product_code LIKE %s' in query
        assert 'category LIKE %s' in query
        assert 'part_numbers LIKE %s' in query
        
        # Should have relevance sorting
        assert 'ORDER BY' in query
        assert 'CASE WHEN' in query
    
    def test_search_products_with_filters(self, service, mock_db, sample_db_rows):
        """Test product search with additional filters"""
        mock_db.execute_query.return_value = [sample_db_rows[0]]
        
        filters = {
            "category": "Electronics",
            "brand": "TestBrand",
            "min_price": 50.0,
            "max_price": 150.0,
            "available_only": True
        }
        
        result = service.search_products('test', filters=filters)
        
        assert len(result['products']) == 1
        assert result['filters_applied'] == filters
        
        # Verify filters were applied to query
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        
        assert 'category = %s' in query
        assert 'brand = %s' in query
        assert 'current_price >= %s' in query
        assert 'current_price <= %s' in query
        assert 'is_available = TRUE' in query
    
    def test_search_products_empty_query(self, service, mock_db):
        """Test product search with empty query"""
        with pytest.raises(ValueError) as exc_info:
            service.search_products('')
        
        assert "Search query is required" in str(exc_info.value)
    
    def test_search_products_whitespace_query(self, service, mock_db):
        """Test product search with whitespace-only query"""
        with pytest.raises(ValueError) as exc_info:
            service.search_products('   ')
        
        assert "Search query is required" in str(exc_info.value)
    
    def test_search_products_database_error(self, service, mock_db):
        """Test product search when database raises exception"""
        mock_db.execute_query.side_effect = Exception("Search index error")
        
        with pytest.raises(Exception) as exc_info:
            service.search_products('test')
        
        assert "Search index error" in str(exc_info.value)

    # Test get_products_by_category method
    def test_get_products_by_category_success(self, service, mock_db, sample_db_rows):
        """Test successful product retrieval by category"""
        electronics_products = [row for row in sample_db_rows if row[2] == 'Electronics']
        mock_db.execute_query.return_value = electronics_products
        
        result = service.get_products_by_category('Electronics')
        
        assert len(result) == 1
        assert result[0]['category'] == 'Electronics'
        
        # Verify query
        call_args = mock_db.execute_query.call_args
        assert 'category = %s' in call_args[0][0]
        assert 'is_available = TRUE' in call_args[0][0]
        assert call_args[0][1] == ['Electronics']
    
    def test_get_products_by_category_empty_category(self, service, mock_db):
        """Test product retrieval with empty category"""
        with pytest.raises(ValueError) as exc_info:
            service.get_products_by_category('')
        
        assert "Category is required" in str(exc_info.value)
    
    def test_get_products_by_category_not_found(self, service, mock_db):
        """Test product retrieval for non-existent category"""
        mock_db.execute_query.return_value = []
        
        result = service.get_products_by_category('NonExistentCategory')
        
        assert len(result) == 0

    # Test get_products_by_brand method
    def test_get_products_by_brand_success(self, service, mock_db, sample_db_rows):
        """Test successful product retrieval by brand"""
        brand_products = [row for row in sample_db_rows if row[3] == 'TestBrand']
        mock_db.execute_query.return_value = brand_products
        
        result = service.get_products_by_brand('TestBrand')
        
        assert len(result) == 1
        assert result[0]['brand'] == 'TestBrand'
        
        # Verify query
        call_args = mock_db.execute_query.call_args
        assert 'brand = %s' in call_args[0][0]
        assert 'is_available = TRUE' in call_args[0][0]
        assert call_args[0][1] == ['TestBrand']
    
    def test_get_products_by_brand_empty_brand(self, service, mock_db):
        """Test product retrieval with empty brand"""
        with pytest.raises(ValueError) as exc_info:
            service.get_products_by_brand('')
        
        assert "Brand is required" in str(exc_info.value)

    # Test get_product_statistics method
    def test_get_product_statistics_success(self, service, mock_db):
        """Test successful product statistics retrieval"""
        # Mock multiple query results
        mock_db.execute_query.side_effect = [
            [(100,)],  # Total products
            [(85,)],   # Available products
            [('Electronics', 30), ('Tools', 25), ('Hardware', 20)],  # Categories
            [('Brand1', 40), ('Brand2', 30), ('Brand3', 15)],  # Brands
            [(10.99, 999.99, 125.50, 20, 45, 20)]  # Price statistics
        ]
        
        result = service.get_product_statistics()
        
        assert result['total_products'] == 100
        assert result['available_products'] == 85
        assert result['unavailable_products'] == 15
        assert len(result['categories']) == 3
        assert len(result['top_brands']) == 3
        assert 'price_statistics' in result
        
        price_stats = result['price_statistics']
        assert price_stats['min_price'] == 10.99
        assert price_stats['max_price'] == 999.99
        assert price_stats['avg_price'] == 125.50
        assert price_stats['price_ranges']['under_100'] == 20
        assert price_stats['price_ranges']['between_100_500'] == 45
        assert price_stats['price_ranges']['over_500'] == 20
    
    def test_get_product_statistics_no_products(self, service, mock_db):
        """Test product statistics when no products exist"""
        mock_db.execute_query.side_effect = [
            [(0,)],  # Total products
            [(0,)],  # Available products
            [],      # Categories
            [],      # Brands
            [(None, None, None, 0, 0, 0)]  # Price statistics
        ]
        
        result = service.get_product_statistics()
        
        assert result['total_products'] == 0
        assert result['available_products'] == 0
        assert result['unavailable_products'] == 0
        assert len(result['categories']) == 0
        assert len(result['top_brands']) == 0
        assert result['price_statistics'] == {}

    # Test validate_product_data method
    def test_validate_product_data_valid(self, service):
        """Test product data validation with valid data"""
        valid_data = {
            "product_code": "PROD001",
            "description": "This is a valid product description with enough characters",
            "category": "Electronics",
            "brand": "TestBrand",
            "current_price": 99.99,
            "quantity_available": 10,
            "unit_of_measure": "EA"
        }
        
        is_valid, errors = service.validate_product_data(valid_data)
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_validate_product_data_missing_required_fields(self, service):
        """Test product data validation with missing required fields"""
        invalid_data = {
            "description": "Test product",
            "category": "Electronics"
            # Missing product_code, brand, current_price
        }
        
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert len(errors) >= 3
        assert any("product_code" in error for error in errors)
        assert any("brand" in error for error in errors)
        assert any("current_price" in error for error in errors)
    
    def test_validate_product_data_empty_fields(self, service):
        """Test product data validation with empty string fields"""
        invalid_data = {
            "product_code": "",
            "description": "   ",
            "category": "Electronics",
            "brand": "TestBrand",
            "current_price": 99.99
        }
        
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert any("product_code" in error and "empty" in error for error in errors)
        assert any("description" in error and "empty" in error for error in errors)
    
    def test_validate_product_data_invalid_product_code(self, service):
        """Test product data validation with invalid product code"""
        invalid_data = {
            "product_code": "AB",  # Too short
            "description": "Valid description with enough characters",
            "category": "Electronics",
            "brand": "TestBrand",
            "current_price": 99.99
        }
        
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert any("3 characters" in error for error in errors)
        
        # Test invalid characters
        invalid_data["product_code"] = "PROD@001"
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert any("letters, numbers, hyphens, and underscores" in error for error in errors)
    
    def test_validate_product_data_invalid_price(self, service):
        """Test product data validation with invalid prices"""
        # Negative price
        invalid_data = {
            "product_code": "PROD001",
            "description": "Valid description with enough characters",
            "category": "Electronics",
            "brand": "TestBrand",
            "current_price": -10.50
        }
        
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert any("negative" in error for error in errors)
        
        # Price too high
        invalid_data["current_price"] = 1000000.00
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert any("999,999.99" in error for error in errors)
        
        # Invalid price format
        invalid_data["current_price"] = "not_a_number"
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert any("valid number" in error for error in errors)
    
    def test_validate_product_data_invalid_quantity(self, service):
        """Test product data validation with invalid quantities"""
        invalid_data = {
            "product_code": "PROD001",
            "description": "Valid description with enough characters",
            "category": "Electronics",
            "brand": "TestBrand",
            "current_price": 99.99,
            "quantity_available": -5
        }
        
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert any("Quantity cannot be negative" in error for error in errors)
        
        # Quantity too high
        invalid_data["quantity_available"] = 1000000
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert any("999,999" in error for error in errors)
    
    def test_validate_product_data_invalid_description(self, service):
        """Test product data validation with invalid descriptions"""
        # Description too short
        invalid_data = {
            "product_code": "PROD001",
            "description": "Short",
            "category": "Electronics",
            "brand": "TestBrand",
            "current_price": 99.99
        }
        
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert any("10 characters" in error for error in errors)
        
        # Description too long
        invalid_data["description"] = "x" * 1001
        is_valid, errors = service.validate_product_data(invalid_data)
        
        assert is_valid == False
        assert any("1000 characters" in error for error in errors)

    # Test get_categories method
    def test_get_categories_success(self, service, mock_db):
        """Test successful categories retrieval"""
        mock_db.execute_query.return_value = [
            ('Electronics',),
            ('Tools',),
            ('Hardware',),
            ('Software',)
        ]
        
        result = service.get_categories()
        
        assert len(result) == 4
        assert 'Electronics' in result
        assert 'Tools' in result
        assert 'Hardware' in result
        assert 'Software' in result
        
        # Verify query
        call_args = mock_db.execute_query.call_args
        assert 'DISTINCT category' in call_args[0][0]
        assert 'ORDER BY category' in call_args[0][0]
    
    def test_get_categories_empty(self, service, mock_db):
        """Test categories retrieval when no categories exist"""
        mock_db.execute_query.return_value = []
        
        result = service.get_categories()
        
        assert len(result) == 0
    
    def test_get_categories_with_nulls(self, service, mock_db):
        """Test categories retrieval filtering out null/empty values"""
        mock_db.execute_query.return_value = [
            ('Electronics',),
            ('',),  # Empty string
            ('Tools',),
            (None,)  # None value
        ]
        
        result = service.get_categories()
        
        assert len(result) == 2
        assert 'Electronics' in result
        assert 'Tools' in result

    # Test get_brands method
    def test_get_brands_success(self, service, mock_db):
        """Test successful brands retrieval"""
        mock_db.execute_query.return_value = [
            ('Brand1',),
            ('Brand2',),
            ('Brand3',)
        ]
        
        result = service.get_brands()
        
        assert len(result) == 3
        assert 'Brand1' in result
        assert 'Brand2' in result
        assert 'Brand3' in result
        
        # Verify query
        call_args = mock_db.execute_query.call_args
        assert 'DISTINCT brand' in call_args[0][0]
        assert 'ORDER BY brand' in call_args[0][0]
    
    def test_get_brands_empty(self, service, mock_db):
        """Test brands retrieval when no brands exist"""
        mock_db.execute_query.return_value = []
        
        result = service.get_brands()
        
        assert len(result) == 0

    # Integration and edge case tests
    def test_database_connection_import_error(self, service):
        """Test handling of database import errors"""
        with patch('backend.application.services.product_service.DatabaseConnection', side_effect=ImportError):
            with pytest.raises(Exception) as exc_info:
                service.get_products()
            
            assert "Database utilities not available" in str(exc_info.value)
    
    def test_logging_on_errors(self, service, mock_db):
        """Test that errors are properly logged"""
        mock_db.execute_query.side_effect = Exception("Test error")
        
        with patch.object(service.logger, 'error') as mock_logger:
            with pytest.raises(Exception):
                service.get_products()
            
            mock_logger.assert_called_once()
            assert "Error getting products" in mock_logger.call_args[0][0]
    
    def test_concurrent_database_operations(self, service, mock_db, sample_db_rows):
        """Test handling of concurrent database operations"""
        # Simulate multiple concurrent calls
        mock_db.execute_query.side_effect = [
            [(len(sample_db_rows),)],  # Count
            sample_db_rows,            # Products
            [sample_db_rows[0]],       # Single product
            [('Electronics',), ('Tools',)],  # Categories
            [('Brand1',), ('Brand2',)]        # Brands
        ]
        
        # Execute multiple operations
        products_result = service.get_products()
        product_result = service.get_product_by_code('PROD001')
        categories_result = service.get_categories()
        brands_result = service.get_brands()
        
        # All operations should succeed
        assert len(products_result['products']) == 3
        assert product_result['product_code'] == 'PROD001'
        assert len(categories_result) == 2
        assert len(brands_result) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
'''

# Test configuration file
conftest_content = '''"""
Pytest Configuration and Shared Fixtures

This file contains shared pytest configuration, fixtures, and utilities
for the Products API and Service test suites.

Shared Fixtures:
- Database mocking utilities
- Sample data generators
- Test client configurations
- Common test utilities

Usage:
    Automatically loaded by pytest when running tests

Author: Development Team
Version: 1.0
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add project root to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def test_database_config():
    """Test database configuration"""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "test_marketplace",
        "user": "test_user",
        "password": "test_password"
    }


@pytest.fixture
def mock_database_connection():
    """Mock database connection for all tests"""
    with patch('backend.application.utils.database.DatabaseConnection') as mock_db_class:
        mock_db = Mock()
        mock_db.connect.return_value = True
        mock_db.execute_query.return_value = []
        mock_db.disconnect.return_value = None
        mock_db_class.return_value = mock_db
        yield mock_db


@pytest.fixture
def sample_product_data():
    """Generate sample product data for testing"""
    return {
        "valid_product": {
            "product_code": "TEST001",
            "description": "Test Product for Unit Testing with Sufficient Description Length",
            "category": "Test Category",
            "brand": "Test Brand",
            "current_price": 99.99,
            "quantity_available": 10,
            "unit_of_measure": "EA",
            "part_numbers": ["PN001", "PN002"],
            "is_available": True
        },
        "minimal_product": {
            "product_code": "MIN001",
            "description": "Minimal test product with required fields only",
            "category": "Minimal",
            "brand": "MinBrand",
            "current_price": 1.00
        },
        "invalid_product": {
            "product_code": "",  # Invalid: empty
            "description": "Short",  # Invalid: too short
            "category": "Test",
            "brand": "Test",
            "current_price": -10.00  # Invalid: negative
        }
    }


@pytest.fixture
def sample_database_rows():
    """Sample database rows in the format returned by database queries"""
    return [
        # (product_code, description, category, brand, price, quantity, uom, part_numbers, is_available)
        ('PROD001', 'Premium Laptop Computer', 'Electronics', 'TechBrand', 1299.99, 15, 'EA', '["LT001", "LT002"]', True),
        ('PROD002', 'Wireless Mouse', 'Electronics', 'TechBrand', 29.99, 50, 'EA', '["MS001"]', True),
        ('PROD003', 'Mechanical Keyboard', 'Electronics', 'KeyboardCorp', 89.99, 25, 'EA', '["KB001", "KB002", "KB003"]', True),
        ('PROD004', 'USB Cable 6ft', 'Electronics', 'CableCo', 12.99, 100, 'EA', '["USB6FT"]', True),
        ('PROD005', 'Power Drill', 'Tools', 'ToolMaster', 79.99, 8, 'EA', '["PD001"]', True),
        ('PROD006', 'Screwdriver Set', 'Tools', 'ToolMaster', 24.99, 20, 'SET', '["SD001", "SD002"]', True),
        ('PROD007', 'Hammer', 'Tools', 'BuildRight', 19.99, 30, 'EA', '["HM001"]', True),
        ('PROD008', 'Office Chair', 'Furniture', 'ComfortSeating', 199.99, 5, 'EA', '["OC001"]', True),
        ('PROD009', 'Desk Lamp', 'Furniture', 'LightCorp', 45.99, 12, 'EA', '["DL001"]', True),
        ('PROD010', 'Out of Stock Item', 'Electronics', 'TechBrand', 99.99, 0, 'EA', '["OOS001"]', False)
    ]


@pytest.fixture
def performance_test_data():
    """Generate large dataset for performance testing"""
    products = []
    for i in range(1000):
        products.append((
            f'PERF{i:04d}',
            f'Performance Test Product {i}',
            f'Category{i % 10}',
            f'Brand{i % 20}',
            round(10.00 + (i * 0.99), 2),
            i % 100,
            'EA',
            f'["PN{i:04d}"]',
            i % 10 != 0  # 90% available
        ))
    return products


@pytest.fixture
def api_test_headers():
    """Standard headers for API testing"""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'ProductsAPI-TestSuite/1.0'
    }


@pytest.fixture
def mock_logging():
    """Mock logging to capture log messages in tests"""
    with patch('backend.application.services.product_service.logging') as mock_log:
        mock_logger = Mock()
        mock_log.getLogger.return_value = mock_logger
        yield mock_logger


# Test utilities
def assert_valid_product_structure(product_dict):
    """Assert that a product dictionary has the expected structure"""
    required_fields = [
        'product_code', 'description', 'category', 'brand', 
        'price', 'quantity_available', 'unit_of_measure', 
        'part_numbers', 'is_available'
    ]
    
    for field in required_fields:
        assert field in product_dict, f"Missing required field: {field}"
    
    # Type checks
    assert isinstance(product_dict['product_code'], str)
    assert isinstance(product_dict['description'], str)
    assert isinstance(product_dict['category'], str)
    assert isinstance(product_dict['brand'], str)
    assert isinstance(product_dict['price'], (int, float))
    assert isinstance(product_dict['quantity_available'], int)
    assert isinstance(product_dict['unit_of_measure'], str)
    assert isinstance(product_dict['is_available'], bool)


def assert_valid_pagination_structure(pagination_dict):
    """Assert that a pagination dictionary has the expected structure"""
    required_fields = ['current_page', 'total_pages', 'total_items', 'items_per_page']
    
    for field in required_fields:
        assert field in pagination_dict, f"Missing required pagination field: {field}"
        assert isinstance(pagination_dict[field], int), f"Field {field} should be integer"
    
    # Logical checks
    assert pagination_dict['current_page'] >= 1
    assert pagination_dict['total_pages'] >= 0
    assert pagination_dict['total_items'] >= 0
    assert pagination_dict['items_per_page'] > 0


def create_mock_db_response(rows, count=None):
    """Create a mock database response for testing"""
    if count is None:
        count = len(rows)
    
    def side_effect(*args, **kwargs):
        query = args[0].lower()
        if 'count(*)' in query:
            return [(count,)]
        else:
            return rows
    
    return side_effect


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to performance tests
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Add database marker to database tests
        if "database" in item.nodeid or "db" in item.nodeid:
            item.add_marker(pytest.mark.database)

# Test requirements file
requirements_content = '''# Test Requirements for Products API and Service
# Install with: pip install -r test_requirements.txt

# Core testing framework
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-xdist>=3.0.0  # For parallel test execution

# Flask testing utilities
pytest-flask>=1.2.0

# Mock and testing utilities
mock>=4.0.0
responses>=0.23.0  # For HTTP mocking
factory-boy>=3.2.0  # For test data generation

# Database testing
pytest-postgresql>=4.1.0  # For PostgreSQL testing
sqlalchemy-utils>=0.40.0  # Database utilities

# Performance testing
pytest-benchmark>=4.0.0
memory-profiler>=0.60.0

# Code quality and coverage
flake8>=6.0.0
black>=23.0.0
isort>=5.12.0
mypy>=1.0.0

# Documentation testing
pytest-doctestplus>=0.12.0

# Async testing (if needed)
pytest-asyncio>=0.21.0

# Reporting
pytest-html>=3.1.0  # HTML test reports
pytest-json-report>=1.5.0  # JSON test reports

# Development utilities
ipdb>=0.13.0  # Debugging
freezegun>=1.2.0  # Time mocking
'''

# Create all test files
with open('test_products_api.py', 'w') as f:
    f.write(api_test_content)

with open('test_product_service.py', 'w') as f:
    f.write(service_test_content)

with open('conftest.py', 'w') as f:
    f.write(conftest_content)

with open('test_requirements.txt', 'w') as f:
    f.write(requirements_content)

print("✅ Created comprehensive test files:")
print("📄 test_products_api.py - API endpoint tests")
print("📄 test_product_service.py - Service layer tests") 
print("📄 conftest.py - Shared fixtures and configuration")
print("📄 test_requirements.txt - Test dependencies")
print("\n🚀 To run the tests:")
print("pip install -r test_requirements.txt")
print("pytest test_products_api.py -v")
print("pytest test_product_service.py -v")
print("pytest --cov=backend --cov-report=html")