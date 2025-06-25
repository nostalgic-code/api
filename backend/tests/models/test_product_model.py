# tests/models/test_product_model.py
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from application.models.product import Product
from datetime import datetime

def test_from_api_response():
    api_product = {
        "product_code": "P001",
        "description": "Test product",
        "category": "TestCat",
        "brand": "TestBrand",
        "base_retail": 100,
        "qoh": 5,
        "uom": "EA",
        "oem_number": "OEM123"
    }
    product = Product.from_api_response(api_product)
    assert product.product_code == "P001"
    assert product.is_available is True
    assert "OEM123" in product.part_numbers

def test_to_dict():
    product = Product(
        id=1,
        product_code="P001",
        description="Test",
        category="Cat",
        brand="Brand",
        base_price=10,
        current_price=12,
        quantity_available=2,
        branch_code="B1",
        is_available=True,
        part_numbers='["PN1"]',
        unit_of_measure="EA",
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )
    d = product.to_dict()
    assert d["product_code"] == "P001"
    assert d["part_numbers"] == ["PN1"]