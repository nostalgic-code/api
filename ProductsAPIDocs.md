# Products API Reference

## Overview

The Products API provides comprehensive endpoints for managing and retrieving product information in the B2B marketplace platform. All endpoints require authentication and appropriate permissions.

## Base URL
```
/api/products
```

## Authentication

All endpoints require a valid Bearer token in the Authorization header:
```
Authorization: Bearer <token>
```

## Permissions

- **Read Operations**: Require `products.read` permission
- **Write Operations**: Require `products.create` permission
- **Admin Operations**: Require platform user authentication

## Endpoints

### 1. List Products

**Endpoint:** `GET /products`

**Permissions:** `products.read`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number |
| limit | integer | 20 | Items per page (max: 100) |
| available_only | boolean | true | Show only available products |
| category | string | - | Filter by category |
| brand | string | - | Filter by brand |
| min_price | float | - | Minimum price filter |
| max_price | float | - | Maximum price filter |
| sort_by | string | - | Sort order: `price_asc`, `price_desc`, `name_asc`, `name_desc` |
| search | string | - | Simple text search (searches in description, brand, product_code) |

**Success Response (200):**
```json
{
  "products": [
    {
      "product_code": "ELEC-001",
      "description": "High-Performance Laptop",
      "category": "electronics",
      "brand": "TechBrand",
      "price": 999.99,
      "quantity_available": 50,
      "unit_of_measure": "EA",
      "part_numbers": ["TB-LP-001", "TB-LP-001-B"],
      "is_available": true
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 95,
    "items_per_page": 20,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "category": "electronics",
    "sort_by": "price_asc"
  }
}
```

---

### 2. Search Products

**Endpoint:** `GET /products/search`

**Permissions:** `products.read`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q, query, or search | string | Yes | Search query |
| page | integer | No | Page number (default: 1) |
| limit | integer | No | Items per page (default: 20, max: 100) |
| available_only | boolean | No | Show only available products (default: true) |
| category | string | No | Filter by category |
| brand | string | No | Filter by brand |
| min_price | float | No | Minimum price filter |
| max_price | float | No | Maximum price filter |
| sort_by | string | No | Sort order (relevance is default) |

**Success Response (200):**
```json
{
  "products": [...],
  "pagination": {...},
  "query": "laptop",
  "search_suggestions": [
    "laptop cases",
    "laptop chargers",
    "laptop stands",
    "laptop bags",
    "laptop screens"
  ],
  "filters_applied": {
    "available_only": true
  }
}
```

---

### 3. Get Filter Options

**Endpoint:** `GET /products/filters`

**Permissions:** `products.read`

**Success Response (200):**
```json
{
  "categories": [
    "electronics",
    "office supplies",
    "furniture",
    "software"
  ],
  "brands": [
    "TechBrand",
    "OfficeMax",
    "ErgoDesign",
    "SoftCorp"
  ],
  "price_range": {
    "min": 0.99,
    "max": 9999.99
  },
  "sort_options": [
    {"value": "relevance", "label": "Relevance"},
    {"value": "price_asc", "label": "Price: Low to High"},
    {"value": "price_desc", "label": "Price: High to Low"},
    {"value": "name_asc", "label": "Name: A to Z"},
    {"value": "name_desc", "label": "Name: Z to A"}
  ]
}
```

---

### 4. Get Product Details

**Endpoint:** `GET /products/<product_code>`

**Permissions:** `products.read`

**Path Parameters:**
- `product_code` (string): The product code to retrieve

**Success Response (200):**
```json
{
  "product_code": "ELEC-001",
  "description": "High-Performance Laptop",
  "category": "electronics",
  "brand": "TechBrand",
  "price": 999.99,
  "quantity_available": 50,
  "unit_of_measure": "EA",
  "part_numbers": ["TB-LP-001", "TB-LP-001-B"],
  "is_available": true
}
```

**Error Response (404):**
```json
{
  "error": "Product not found"
}
```

---

### 5. Get Related Products

**Endpoint:** `GET /products/<product_code>/related`

**Permissions:** `products.read`

**Path Parameters:**
- `product_code` (string): The base product code

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 5 | Maximum number of related products (max: 20) |

**Success Response (200):**
```json
{
  "product_code": "ELEC-001",
  "related_products": [
    {
      "product_code": "ELEC-002",
      "description": "Laptop Carrying Case",
      "category": "electronics",
      "brand": "TechBrand",
      "price": 49.99,
      "quantity_available": 200,
      "unit_of_measure": "EA",
      "part_numbers": ["TB-LC-001"],
      "is_available": true
    }
  ],
  "count": 1
}
```

---

### 6. Get Product Statistics (Admin Only)

**Endpoint:** `GET /products/statistics`

**Permissions:** Platform user only

**Success Response (200):**
```json
{
  "timestamp": "2024-06-24T10:30:00Z",
  "summary": {
    "total_products": 1500,
    "available_products": 1200,
    "out_of_stock": 150,
    "low_stock": 150
  },
  "by_category": [
    {
      "category": "electronics",
      "count": 500,
      "average_price": 299.99
    }
  ],
  "by_brand": [
    {
      "brand": "TechBrand",
      "count": 200
    }
  ],
  "price_distribution": {
    "min": 0.99,
    "max": 9999.99,
    "average": 199.99,
    "median": 149.99
  }
}
```

---

### 7. Autocomplete Suggestions

**Endpoint:** `GET /products/autocomplete`

**Permissions:** `products.read`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q, query, or search | string | Yes | Partial search string (min 2 chars) |
| limit | integer | No | Maximum suggestions (default: 5, max: 10) |

**Success Response (200):**
```json
{
  "suggestions": [
    "laptop",
    "laptop cases",
    "laptop chargers",
    "laptop stands",
    "laptop bags"
  ]
}
```

---

### 8. Validate Product Data

**Endpoint:** `POST /products/validate`

**Permissions:** `products.create`

**Request Body:**
```json
{
  "product_code": "NEW-001",
  "description": "New Product Description",
  "category": "electronics",
  "brand": "NewBrand",
  "current_price": 99.99,
  "quantity_available": 100
}
```

**Success Response (200):**
```json
{
  "is_valid": true,
  "errors": []
}
```

**Error Response (400):**
```json
{
  "is_valid": false,
  "errors": [
    "Field 'description' must be at least 10 characters long",
    "Price cannot be negative"
  ]
}
```

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200 OK` - Successful request
- `400 Bad Request` - Invalid parameters or request data
- `401 Unauthorized` - Missing or invalid authentication token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error