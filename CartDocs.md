# 🛒 Cart API Documentation

## Overview

This API provides endpoints for managing a user's shopping cart, including adding, updating, retrieving, and removing items. It is built using Flask and relies on a `CartService` class for business logic.

---

## Base URL
---

## Endpoints

### `GET /cart/`

**Description:**  
Retrieve all cart items for a user.

**Query Parameters:**

- `customer_user_id` (required): The user's ID.

**Response:**

- `200 OK` with cart data  
- `400 Bad Request` if `customer_user_id` is missing

---

### `GET /cart/item`

**Description:**  
Retrieve a specific cart item.

**Query Parameters:**

- `customer_user_id` (required): The user's ID  
- `product_code` (required): The product code

**Response:**

- `200 OK` with item data  
- `400 Bad Request` if required parameters are missing

---

### `POST /cart/item`

**Description:**  
Add or update a cart item.

**JSON Body:**

- `customer_user_id` (required): The user's ID  
- `product_code` (required): The product code  
- `quantity` (optional, default=1): Quantity to set

**Response:**

- `200 OK` with result if successful  
- `400 Bad Request` if parameters are missing or invalid

---

### `GET /cart/count`

**Description:**  
Get the total number of items in the user's cart.

**Query Parameters:**

- `customer_user_id` (required): The user's ID

**Response:**

- `200 OK` with count  
- `400 Bad Request` if parameter is missing

---

### `POST /cart/add`

**Description:**  
Add an item to the cart (legacy endpoint, increments quantity).

**JSON Body:**

- `customer_user_id` (required): The user's ID  
- `product_code` (required): The product code  
- `quantity` (optional, default=1): Quantity to add

**Response:**

- `200 OK` with result if successful  
- `400 Bad Request` if parameters are missing or invalid

---

### `PUT /cart/update`

**Description:**  
Update the quantity of a cart item.

**JSON Body:**

- `customer_user_id` (required): The user's ID  
- `product_code` (required): The product code  
- `quantity` (required): New quantity (if 0, item is removed)

**Response:**

- `200 OK` with result if successful  
- `400 Bad Request` if parameters are missing or invalid

---

### `DELETE /cart/item`

**Description:**  
Remove a specific item from the cart.

**JSON Body:**

- `customer_user_id` (required): The user's ID  
- `product_code` (required): The product code

**Response:**

- `200 OK` with result if successful  
- `400 Bad Request` if parameters are missing

---

### `DELETE /cart/clear`

**Description:**  
Clear all items from the user's cart.

**JSON Body:**

- `customer_user_id` (required): The user's ID

**Response:**

- `200 OK` with result if successful  
- `400 Bad Request` if parameter is missing

---

### `POST /cart/save`

**Description:**  
Save the entire cart (legacy endpoint, replaces all items).

**JSON Body:**

- `customer_user_id` (required): The user's ID  
- `items` (optional, default=[]): List of items to save

**Response:**

- `200 OK` with result if successful  
- `400 Bad Request` if parameter is missing

---

## CartService Class

Handles all business logic for cart operations.

### Methods

- `get_cart(user_id: int) → dict | None`  
  Get the complete cart for a user.

- `get_cart_item(user_id: str, product_code: str) → dict | None`  
  Get a specific cart item for a user.

- `save_cart_item(user_id: str, product_code: str, quantity: int) → dict`  
  Add or update a cart item. Creates the cart if it does not exist.

- `get_cart_item_count(user_id: str) → int`  
  Get the total quantity of items in the user's cart.

- `add_to_cart(user_id: str, product_code: str, quantity: int) → dict`  
  Add an item to the cart, incrementing quantity if it already exists.

- `remove_cart_item(user_id: str, product_code: str) → dict`  
  Remove a specific item from the cart.

- `clear_cart(user_id: str) → dict`  
  Remove all items from the user's cart.

- `save_cart(user_id: str, items: list) → dict`  
  Replace the user's cart with a new list of items.

- `update_cart_item(user_id: str, product_code: str, quantity: int) → dict`  
  Update the quantity of a specific cart item. Removes the item if quantity is 0.

---

## Error Handling

All endpoints return a JSON error message and a `400` status code if required parameters are missing or invalid. Service methods return a dictionary with a `success` boolean and a `message` or `data` field.

---

## Example Cart Item JSON

```json
{
  "cart_id": 123,
  "product_code": "ABC123",
  "product_name": "Product Name",
  "quantity": 2,
  "price": 99.99,
  "depot_code": "DEPOT1"
}