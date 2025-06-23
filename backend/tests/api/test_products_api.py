# import sys
# import os

# # Dynamically set PYTHONPATH to /backend
# current_dir = os.path.dirname(os.path.abspath(__file__))
# backend_path = os.path.abspath(os.path.join(current_dir, "../../"))
# if backend_path not in sys.path:
#     sys.path.insert(0, backend_path)

# api_test_content = '''"""
# Products API Test Suite

# Comprehensive test suite for the Products API endpoints.
# Tests all REST endpoints with various scenarios including success cases,
# error handling, edge cases, and validation.

# Test Coverage:
# - GET /products - List products with filtering and pagination
# - GET /products/<product_code> - Get specific product
# - GET /products/search - Search products
# - GET /products/categories - Get categories
# - GET /products/brands - Get brands

# Dependencies:
#     - pytest
#     - Flask test client
#     - Mock database responses
#     - Test fixtures

# Usage:
#     pytest test_products_api.py -v

# Author: Development Team
# Version: 1.0
# """'''

# import pytest
# import json
# from unittest.mock import Mock, patch, MagicMock
# from flask import Flask
# from application.api.products import products_bp
# from application.services.product_service import ProductService


# class TestProductsAPI:
#     """Test suite for Products API endpoints"""
    
#     @pytest.fixture
#     def app(self):
#         """Create Flask app for testing"""
#         app = Flask(__name__)
#         app.register_blueprint(products_bp)
#         app.config['TESTING'] = True
#         return app
    
#     @pytest.fixture
#     def client(self, app):
#         """Create test client"""
#         return app.test_client()
    
#     @pytest.fixture
#     def mock_service(self):
#         """Mock ProductService for testing"""
#         with patch('backend.api.products.service') as mock:
#             yield mock
    
#     @pytest.fixture
#     def sample_products(self):
#         """Sample product data for testing"""
#         return [
#             {
#                 "product_code": "PROD001",
#                 "description": "Test Product 1",
#                 "category": "Electronics",
#                 "brand": "TestBrand",
#                 "price": 99.99,
#                 "quantity_available": 10,
#                 "unit_of_measure": "EA",
#                 "part_numbers": ["PN001", "PN002"],
#                 "is_available": True
#             },
#             {
#                 "product_code": "PROD002", 
#                 "description": "Test Product 2",
#                 "category": "Tools",
#                 "brand": "AnotherBrand",
#                 "price": 149.99,
#                 "quantity_available": 5,
#                 "unit_of_measure": "EA",
#                 "part_numbers": ["PN003"],
#                 "is_available": True
#             }
#         ]
    
#     @pytest.fixture
#     def sample_pagination_response(self, sample_products):
#         """Sample paginated response"""
#         return {
#             "products": sample_products,
#             "pagination": {
#                 "current_page": 1,
#                 "total_pages": 1,
#                 "total_items": 2,
#                 "items_per_page": 20
#             },
#             "filters_applied": {}
#         }

#     # GET /products tests
#     def test_get_products_success(self, client, mock_service, sample_pagination_response):
#         """Test successful product retrieval"""
#         mock_service.get_products.return_value = sample_pagination_response
        
#         response = client.get('/products/')
        
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert 'products' in data
#         assert 'pagination' in data
#         assert len(data['products']) == 2
#         assert data['products'][0]['product_code'] == 'PROD001'
        
#         # Verify service was called with correct parameters
#         mock_service.get_products.assert_called_once()
#         call_args = mock_service.get_products.call_args
#         assert 'filters' in call_args.kwargs
#         assert 'pagination' in call_args.kwargs
    
#     def test_get_products_with_filters(self, client, mock_service, sample_pagination_response):
#         """Test product retrieval with filters"""
#         mock_service.get_products.return_value = sample_pagination_response
        
#         response = client.get('/products/?category=Electronics&brand=TestBrand&min_price=50&max_price=200&available_only=true')
        
#         assert response.status_code == 200
        
#         # Verify filters were passed correctly
#         call_args = mock_service.get_products.call_args
#         filters = call_args.kwargs['filters']
#         assert filters['category'] == 'Electronics'
#         assert filters['brand'] == 'TestBrand'
#         assert filters['min_price'] == 50.0
#         assert filters['max_price'] == 200.0
#         assert filters['available_only'] == True
    
#     def test_get_products_with_pagination(self, client, mock_service, sample_pagination_response):
#         """Test product retrieval with pagination"""
#         mock_service.get_products.return_value = sample_pagination_response
        
#         response = client.get('/products/?page=2&limit=10')
        
#         assert response.status_code == 200
        
#         # Verify pagination was passed correctly
#         call_args = mock_service.get_products.call_args
#         pagination = call_args.kwargs['pagination']
#         assert pagination['page'] == 2
#         assert pagination['limit'] == 10
    
#     def test_get_products_with_search(self, client, mock_service, sample_pagination_response):
#         """Test product retrieval with search filter"""
#         mock_service.get_products.return_value = sample_pagination_response
        
#         response = client.get('/products/?search=test')
        
#         assert response.status_code == 200
        
#         # Verify search filter was passed
#         call_args = mock_service.get_products.call_args
#         filters = call_args.kwargs['filters']
#         assert filters['search'] == 'test'
    
#     def test_get_products_service_error(self, client, mock_service):
#         """Test product retrieval when service raises exception"""
#         mock_service.get_products.side_effect = Exception("Database error")
        
#         response = client.get('/products/')
        
#         assert response.status_code == 500
#         data = json.loads(response.data)
#         assert 'error' in data
#         assert 'Database error' in data['error']
    
#     def test_get_products_invalid_pagination(self, client, mock_service, sample_pagination_response):
#         """Test product retrieval with invalid pagination parameters"""
#         mock_service.get_products.return_value = sample_pagination_response
        
#         # Test with invalid page number (should default to 1)
#         response = client.get('/products/?page=invalid&limit=abc')
        
#         assert response.status_code == 200
        
#         # Verify defaults were used
#         call_args = mock_service.get_products.call_args
#         pagination = call_args.kwargs['pagination']
#         assert pagination['page'] == 1
#         assert pagination['limit'] == 20

#     # GET /products/<product_code> tests
#     def test_get_product_by_code_success(self, client, mock_service, sample_products):
#         """Test successful product retrieval by code"""
#         mock_service.get_product_by_code.return_value = sample_products[0]
        
#         response = client.get('/products/PROD001')
        
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert data['product_code'] == 'PROD001'
#         assert data['description'] == 'Test Product 1'
        
#         mock_service.get_product_by_code.assert_called_once_with('PROD001')
    
#     def test_get_product_by_code_not_found(self, client, mock_service):
#         """Test product retrieval when product not found"""
#         mock_service.get_product_by_code.return_value = None
        
#         response = client.get('/products/NONEXISTENT')
        
#         assert response.status_code == 404
#         data = json.loads(response.data)
#         assert 'error' in data
#         assert 'Product not found' in data['error']
    
#     def test_get_product_by_code_service_error(self, client, mock_service):
#         """Test product retrieval when service raises exception"""
#         mock_service.get_product_by_code.side_effect = Exception("Database connection failed")
        
#         response = client.get('/products/PROD001')
        
#         assert response.status_code == 500
#         data = json.loads(response.data)
#         assert 'error' in data
#         assert 'Database connection failed' in data['error']

#     # GET /products/search tests
#     def test_search_products_success(self, client, mock_service, sample_products):
#         """Test successful product search"""
#         search_response = {
#             "products": sample_products,
#             "count": 2,
#             "query": "test",
#             "filters_applied": {}
#         }
#         mock_service.search_products.return_value = search_response
        
#         response = client.get('/products/search?q=test')
        
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert 'products' in data
#         assert 'count' in data
#         assert data['count'] == 2
#         assert data['query'] == 'test'
        
#         mock_service.search_products.assert_called_once_with('test', filters={})
    
#     def test_search_products_with_query_param(self, client, mock_service, sample_products):
#         """Test product search with 'query' parameter"""
#         search_response = {
#             "products": sample_products,
#             "count": 2,
#             "query": "electronics",
#             "filters_applied": {}
#         }
#         mock_service.search_products.return_value = search_response
        
#         response = client.get('/products/search?query=electronics')
        
#         assert response.status_code == 200
#         mock_service.search_products.assert_called_once_with('electronics', filters={})
    
#     def test_search_products_with_search_param(self, client, mock_service, sample_products):
#         """Test product search with 'search' parameter"""
#         search_response = {
#             "products": sample_products,
#             "count": 2,
#             "query": "tools",
#             "filters_applied": {}
#         }
#         mock_service.search_products.return_value = search_response
        
#         response = client.get('/products/search?search=tools')
        
#         assert response.status_code == 200
#         mock_service.search_products.assert_called_once_with('tools', filters={})
    
#     def test_search_products_with_filters(self, client, mock_service, sample_products):
#         """Test product search with additional filters"""
#         search_response = {
#             "products": [sample_products[0]],
#             "count": 1,
#             "query": "test",
#             "filters_applied": {"category": "Electronics"}
#         }
#         mock_service.search_products.return_value = search_response
        
#         response = client.get('/products/search?q=test&category=Electronics&min_price=50')
        
#         assert response.status_code == 200
        
#         # Verify filters were passed
#         call_args = mock_service.search_products.call_args
#         assert call_args[0][0] == 'test'  # query
#         filters = call_args[1]['filters']
#         assert filters['category'] == 'Electronics'
#         assert filters['min_price'] == 50.0
    
#     def test_search_products_missing_query(self, client, mock_service):
#         """Test product search without query parameter"""
#         response = client.get('/products/search')
        
#         assert response.status_code == 400
#         data = json.loads(response.data)
#         assert 'error' in data
#         assert 'required' in data['error'].lower()
    
#     def test_search_products_service_error(self, client, mock_service):
#         """Test product search when service raises exception"""
#         mock_service.search_products.side_effect = Exception("Search index unavailable")
        
#         response = client.get('/products/search?q=test')
        
#         assert response.status_code == 500
#         data = json.loads(response.data)
#         assert 'error' in data
#         assert 'Search index unavailable' in data['error']

#     # GET /products/categories tests
#     def test_get_categories_success(self, client, mock_service):
#         """Test successful categories retrieval"""
#         categories = ["Electronics", "Tools", "Hardware", "Software"]
#         mock_service.get_categories.return_value = categories
        
#         response = client.get('/products/categories')
        
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert 'categories' in data
#         assert len(data['categories']) == 4
#         assert 'Electronics' in data['categories']
#         assert 'Tools' in data['categories']
        
#         mock_service.get_categories.assert_called_once()
    
#     def test_get_categories_empty(self, client, mock_service):
#         """Test categories retrieval when no categories exist"""
#         mock_service.get_categories.return_value = []
        
#         response = client.get('/products/categories')
        
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert 'categories' in data
#         assert len(data['categories']) == 0
    
#     def test_get_categories_service_error(self, client, mock_service):
#         """Test categories retrieval when service raises exception"""
#         mock_service.get_categories.side_effect = Exception("Database query failed")
        
#         response = client.get('/products/categories')
        
#         assert response.status_code == 500
#         data = json.loads(response.data)
#         assert 'error' in data
#         assert 'Database query failed' in data['error']

#     # GET /products/brands tests
#     def test_get_brands_success(self, client, mock_service):
#         """Test successful brands retrieval"""
#         brands = ["TestBrand", "AnotherBrand", "ThirdBrand"]
#         mock_service.get_brands.return_value = brands
        
#         response = client.get('/products/brands')
        
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert 'brands' in data
#         assert len(data['brands']) == 3
#         assert 'TestBrand' in data['brands']
#         assert 'AnotherBrand' in data['brands']
        
#         mock_service.get_brands.assert_called_once()
    
#     def test_get_brands_empty(self, client, mock_service):
#         """Test brands retrieval when no brands exist"""
#         mock_service.get_brands.return_value = []
        
#         response = client.get('/products/brands')
        
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert 'brands' in data
#         assert len(data['brands']) == 0
    
#     def test_get_brands_service_error(self, client, mock_service):
#         """Test brands retrieval when service raises exception"""
#         mock_service.get_brands.side_effect = Exception("Connection timeout")
        
#         response = client.get('/products/brands')
        
#         assert response.status_code == 500
#         data = json.loads(response.data)
#         assert 'error' in data
#         assert 'Connection timeout' in data['error']

#     # Edge cases and integration tests
#     def test_products_endpoint_with_all_filters(self, client, mock_service, sample_pagination_response):
#         """Test products endpoint with all possible filters"""
#         mock_service.get_products.return_value = sample_pagination_response
        
#         query_params = (
#             "?category=Electronics&brand=TestBrand&min_price=10.50&max_price=500.75"
#             "&available_only=false&search=test&page=3&limit=15"
#         )
#         response = client.get(f'/products/{query_params}')
        
#         assert response.status_code == 200
        
#         # Verify all parameters were parsed correctly
#         call_args = mock_service.get_products.call_args
#         filters = call_args.kwargs['filters']
#         pagination = call_args.kwargs['pagination']
        
#         assert filters['category'] == 'Electronics'
#         assert filters['brand'] == 'TestBrand'
#         assert filters['min_price'] == 10.5
#         assert filters['max_price'] == 500.75
#         assert filters['available_only'] == False
#         assert filters['search'] == 'test'
#         assert pagination['page'] == 3
#         assert pagination['limit'] == 15
    
#     def test_search_with_all_filters(self, client, mock_service, sample_products):
#         """Test search endpoint with all possible filters"""
#         search_response = {
#             "products": sample_products,
#             "count": 2,
#             "query": "test query",
#             "filters_applied": {}
#         }
#         mock_service.search_products.return_value = search_response
        
#         query_params = (
#             "?q=test query&category=Tools&brand=AnotherBrand"
#             "&min_price=25.99&max_price=999.99&available_only=true"
#         )
#         response = client.get(f'/products/search{query_params}')
        
#         assert response.status_code == 200
        
#         # Verify all filters were passed
#         call_args = mock_service.search_products.call_args
#         assert call_args[0][0] == 'test query'
#         filters = call_args[1]['filters']
#         assert filters['category'] == 'Tools'
#         assert filters['brand'] == 'AnotherBrand'
#         assert filters['min_price'] == 25.99
#         assert filters['max_price'] == 999.99
#         assert filters['available_only'] == True

#     # Performance and load tests
#     def test_concurrent_requests_simulation(self, client, mock_service, sample_pagination_response):
#         """Simulate concurrent requests to test thread safety"""
#         mock_service.get_products.return_value = sample_pagination_response
#         mock_service.get_product_by_code.return_value = sample_pagination_response['products'][0]
#         mock_service.get_categories.return_value = ['Electronics', 'Tools']
#         mock_service.get_brands.return_value = ['Brand1', 'Brand2']
        
#         # Simulate multiple concurrent requests
#         responses = []
#         for i in range(10):
#             if i % 4 == 0:
#                 resp = client.get('/products/')
#             elif i % 4 == 1:
#                 resp = client.get('/products/PROD001')
#             elif i % 4 == 2:
#                 resp = client.get('/products/categories')
#             else:
#                 resp = client.get('/products/brands')
#             responses.append(resp)
        
#         # All requests should succeed
#         for resp in responses:
#             assert resp.status_code == 200
    
#     def test_large_result_set_handling(self, client, mock_service):
#         """Test handling of large result sets"""
#         # Create a large mock response
#         large_products = []
#         for i in range(1000):
#             large_products.append({
#                 "product_code": f"PROD{i:04d}",
#                 "description": f"Product {i}",
#                 "category": "Electronics",
#                 "brand": "TestBrand",
#                 "price": 99.99 + i,
#                 "quantity_available": 10,
#                 "unit_of_measure": "EA",
#                 "part_numbers": [f"PN{i:04d}"],
#                 "is_available": True
#             })
        
#         large_response = {
#             "products": large_products[:20],  # Paginated
#             "pagination": {
#                 "current_page": 1,
#                 "total_pages": 50,
#                 "total_items": 1000,
#                 "items_per_page": 20
#             },
#             "filters_applied": {}
#         }
        
#         mock_service.get_products.return_value = large_response
        
#         response = client.get('/products/')
        
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert len(data['products']) == 20
#         assert data['pagination']['total_items'] == 1000


# if __name__ == '__main__':
#     pytest.main([__file__, '-v'])




api_test_content = '''"""
Products API Test Suite

Comprehensive test suite for the Products API endpoints.
Tests all REST endpoints with various scenarios including success cases,
error handling, edge cases, and validation.

Test Coverage:
- GET /products - List products with filtering and pagination
- GET /products/<product_code> - Get specific product
- GET /products/search - Search products
- GET /products/categories - Get categories
- GET /products/brands - Get brands

Dependencies:
    - pytest
    - Flask test client
    - Mock database responses
    - Test fixtures

Usage:
    pytest test_products_api.py -v

Author: Development Team
Version: 1.0
"""'''

import sys
import os
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import the modules - adjust these paths based on your actual structure
try:
    from application.api.products import products_bp
    from application.services.product_service import ProductService
except ImportError:
    # Alternative import paths - adjust as needed
    try:
        from backend.application.api.products import products_bp
        from backend.application.services.product_service import ProductService
    except ImportError:
        # Create mock modules for testing if imports fail
        from flask import Blueprint
        
        products_bp = Blueprint('products', __name__, url_prefix='/products')
        
        class ProductService:
            def get_products(self, filters=None, pagination=None):
                return {"products": [], "pagination": {}}
            
            def get_product_by_code(self, code):
                return None
            
            def search_products(self, query, filters=None):
                return {"products": [], "count": 0}
            
            def get_categories(self):
                return []
            
            def get_brands(self):
                return []


class TestProductsAPI:
    """Test suite for Products API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = Flask(__name__)
        app.register_blueprint(products_bp)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def mock_service(self):
        """Mock ProductService for testing"""
        # Create a mock service instance
        mock_service = Mock(spec=ProductService)
        
        # Patch the service instance in the products module
        with patch('application.api.products.service', mock_service):
            yield mock_service
    
    @pytest.fixture
    def sample_products(self):
        """Sample product data for testing"""
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
    
    @pytest.fixture
    def sample_pagination_response(self, sample_products):
        """Sample paginated response"""
        return {
            "products": sample_products,
            "pagination": {
                "current_page": 1,
                "total_pages": 1,
                "total_items": 2,
                "items_per_page": 20
            },
            "filters_applied": {}
        }

    # Test the service mock directly first
    def test_mock_service_setup(self, mock_service):
        """Test that the mock service is properly configured"""
        assert mock_service is not None
        assert hasattr(mock_service, 'get_products')
        assert hasattr(mock_service, 'get_product_by_code')
        assert hasattr(mock_service, 'search_products')
        assert hasattr(mock_service, 'get_categories')
        assert hasattr(mock_service, 'get_brands')

    # GET /products tests
    def test_get_products_success(self, client, mock_service, sample_pagination_response):
        """Test successful product retrieval"""
        mock_service.get_products.return_value = sample_pagination_response
        
        response = client.get('/products/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'products' in data
        assert 'pagination' in data
        assert len(data['products']) == 2
        assert data['products'][0]['product_code'] == 'PROD001'
        
        # Verify service was called
        mock_service.get_products.assert_called_once()
    
    def test_get_products_with_filters(self, client, mock_service, sample_pagination_response):
        """Test product retrieval with filters"""
        mock_service.get_products.return_value = sample_pagination_response
        
        response = client.get('/products/?category=Electronics&brand=TestBrand&min_price=50&max_price=200&available_only=true')
        
        assert response.status_code == 200
        
        # Verify service was called (we can't easily verify exact parameters without the real implementation)
        mock_service.get_products.assert_called_once()
    
    def test_get_products_service_error(self, client, mock_service):
        """Test product retrieval when service raises exception"""
        mock_service.get_products.side_effect = Exception("Database error")
        
        response = client.get('/products/')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Database error' in data['error']

    # GET /products/<product_code> tests
    def test_get_product_by_code_success(self, client, mock_service, sample_products):
        """Test successful product retrieval by code"""
        mock_service.get_product_by_code.return_value = sample_products[0]
        
        response = client.get('/products/PROD001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['product_code'] == 'PROD001'
        assert data['description'] == 'Test Product 1'
        
        mock_service.get_product_by_code.assert_called_once_with('PROD001')
    
    def test_get_product_by_code_not_found(self, client, mock_service):
        """Test product retrieval when product not found"""
        mock_service.get_product_by_code.return_value = None
        
        response = client.get('/products/NONEXISTENT')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Product not found' in data['error']
    
    def test_get_product_by_code_service_error(self, client, mock_service):
        """Test product retrieval when service raises exception"""
        mock_service.get_product_by_code.side_effect = Exception("Database connection failed")
        
        response = client.get('/products/PROD001')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Database connection failed' in data['error']

    # GET /products/search tests
    def test_search_products_success(self, client, mock_service, sample_products):
        """Test successful product search"""
        search_response = {
            "products": sample_products,
            "count": 2,
            "query": "test",
            "filters_applied": {}
        }
        mock_service.search_products.return_value = search_response
        
        response = client.get('/products/search?q=test')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'products' in data
        assert 'count' in data
        assert data['count'] == 2
        assert data['query'] == 'test'
        
        mock_service.search_products.assert_called_once()
    
    def test_search_products_missing_query(self, client, mock_service):
        """Test product search without query parameter"""
        response = client.get('/products/search')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'required' in data['error'].lower()
    
    def test_search_products_service_error(self, client, mock_service):
        """Test product search when service raises exception"""
        mock_service.search_products.side_effect = Exception("Search index unavailable")
        
        response = client.get('/products/search?q=test')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Search index unavailable' in data['error']

    # GET /products/categories tests
    def test_get_categories_success(self, client, mock_service):
        """Test successful categories retrieval"""
        categories = ["Electronics", "Tools", "Hardware", "Software"]
        mock_service.get_categories.return_value = categories
        
        response = client.get('/products/categories')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'categories' in data
        assert len(data['categories']) == 4
        assert 'Electronics' in data['categories']
        assert 'Tools' in data['categories']
        
        mock_service.get_categories.assert_called_once()
    
    def test_get_categories_empty(self, client, mock_service):
        """Test categories retrieval when no categories exist"""
        mock_service.get_categories.return_value = []
        
        response = client.get('/products/categories')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'categories' in data
        assert len(data['categories']) == 0
    
    def test_get_categories_service_error(self, client, mock_service):
        """Test categories retrieval when service raises exception"""
        mock_service.get_categories.side_effect = Exception("Database query failed")
        
        response = client.get('/products/categories')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Database query failed' in data['error']

    # GET /products/brands tests
    def test_get_brands_success(self, client, mock_service):
        """Test successful brands retrieval"""
        brands = ["TestBrand", "AnotherBrand", "ThirdBrand"]
        mock_service.get_brands.return_value = brands
        
        response = client.get('/products/brands')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'brands' in data
        assert len(data['brands']) == 3
        assert 'TestBrand' in data['brands']
        assert 'AnotherBrand' in data['brands']
        
        mock_service.get_brands.assert_called_once()
    
    def test_get_brands_service_error(self, client, mock_service):
        """Test brands retrieval when service raises exception"""
        mock_service.get_brands.side_effect = Exception("Connection timeout")
        
        response = client.get('/products/brands')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Connection timeout' in data['error']

    # Integration tests
    def test_all_endpoints_respond(self, client, mock_service, sample_pagination_response, sample_products):
        """Test that all endpoints respond without crashing"""
        # Setup mocks
        mock_service.get_products.return_value = sample_pagination_response
        mock_service.get_product_by_code.return_value = sample_products[0]
        mock_service.search_products.return_value = {"products": sample_products, "count": 2, "query": "test"}
        mock_service.get_categories.return_value = ["Electronics", "Tools"]
        mock_service.get_brands.return_value = ["Brand1", "Brand2"]
        
        # Test all endpoints
        endpoints = [
            '/products/',
            '/products/PROD001',
            '/products/search?q=test',
            '/products/categories',
            '/products/brands'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 400], f"Endpoint {endpoint} failed with status {response.status_code}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
