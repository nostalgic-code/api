# tests/services/test_product_service.py
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


import pytest
from unittest.mock import patch, MagicMock
from application.services.product_service import ProductService

@pytest.fixture
def service():
    return ProductService()

def test_validate_product_data_valid(service):
    product = {
        "product_code": "ABC123",
        "description": "A valid product description",
        "category": "Electronics",
        "brand": "BrandX",
        "current_price": 99.99,
        "quantity_available": 10
    }
    is_valid, errors = service.validate_product_data(product)
    assert is_valid
    assert errors == []

def test_validate_product_data_missing_fields(service):
    product = {}
    is_valid, errors = service.validate_product_data(product)
    assert not is_valid
    assert "Field 'product_code' is required" in errors


def test_get_products_calls_db(service):
    with patch.object(service, '_get_db_connection') as mock_db:
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn

        # The first call is for the count query, the second is for the products query
        mock_conn.execute_query.side_effect = [
            [(1,)],  # For the count query: SELECT COUNT(*) ...
            [("ABC123", "Desc", "Cat", "Brand", 10.0, 5, "unit", None, True)]  # For the products query
        ]

        result = service.get_products()
        assert "products" in result
        assert result["products"][0]["product_code"] == "ABC123"
