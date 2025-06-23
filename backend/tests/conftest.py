"""
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
