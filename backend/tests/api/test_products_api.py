# tests/api/test_products_api.py

import json

def test_get_products(client, mocker):
    # Mock the ProductService.get_products method
    mocker.patch(
        "application.services.product_service.ProductService.get_products",
        return_value={"products": [{"product_code": "ABC123"}], "pagination": {}}
    )
    response = client.get("/products/")
    assert response.status_code == 200
    data = response.get_json()
    assert "products" in data
    assert data["products"][0]["product_code"] == "ABC123"

def test_search_products_missing_query(client):
    response = client.get("/products/search")
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_validate_product(client, mocker):
    mocker.patch(
        "application.services.product_service.ProductService.validate_product_data",
        return_value=(True, [])
    )
    response = client.post(
        "/products/validate",
        data=json.dumps({"product_code": "X", "description": "desc", "category": "cat", "brand": "b", "current_price": 1}),
        content_type="application/json"
    )
    assert response.status_code == 200
    assert response.get_json()["is_valid"] is True