from flask import Blueprint, request, jsonify
from application.services.cart_service import CartService

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')
cart_service = CartService()

@cart_bp.route('/', methods=['GET'])
def get_cart():
    """Get all cart items for a user"""
    customer_user_id = request.args.get('customer_user_id')

    if not customer_user_id:
        return jsonify({'error': 'customer_user_id is required'}), 400
    
    cart = cart_service.get_cart(customer_user_id)
    return jsonify(cart or {}), 200

@cart_bp.route('/items', methods=['GET'])
def get_cart_items():
    """Get all cart items for a user (alternative endpoint)"""
    customer_user_id = request.args.get('customer_user_id')
    if not customer_user_id:
        return jsonify({'error': 'customer_user_id is required'}), 400
    
    items = cart_service.get_cart_items(customer_user_id)
    return jsonify(items or []), 200

@cart_bp.route('/item', methods=['GET'])
def get_cart_item():
    """Get specific cart item"""
    customer_user_id = request.args.get('customer_user_id')
    product_code = request.args.get('product_code')
    
    if not customer_user_id or not product_code:
        return jsonify({'error': 'customer_user_id and product_code are required'}), 400
    
    item = cart_service.get_cart_item(customer_user_id, product_code)
    return jsonify(item), 200

@cart_bp.route('/item', methods=['POST'])
def save_cart_item():
    """Add or update cart item"""
    data = request.json
    if not data:
        return jsonify({'error': 'JSON data is required'}), 400
    
    customer_user_id = data.get('customer_user_id')
    product_code = data.get('product_code')
    quantity = data.get('quantity', 1)
    
    if not customer_user_id or not product_code:
        return jsonify({'error': 'customer_user_id and product_code are required'}), 400
    
    try:
        quantity = int(quantity)
        if quantity < 1:
            return jsonify({'error': 'quantity must be at least 1'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'quantity must be a valid integer'}), 400
    
    result = cart_service.save_cart_item(customer_user_id, product_code, quantity)
    return jsonify(result), 200 if result.get('success') else 400

@cart_bp.route('/count', methods=['GET'])
def get_cart_count():
    """Get total cart item count"""
    customer_user_id = request.args.get('customer_user_id')
    if not customer_user_id:
        return jsonify({'error': 'customer_user_id is required'}), 400
    
    count = cart_service.get_cart_item_count(customer_user_id)
    return jsonify({'count': count}), 200

@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    """Add item to cart (legacy endpoint)"""
    data = request.json
    if not data:
        return jsonify({'error': 'JSON data is required'}), 400
    
    customer_user_id = data.get('customer_user_id')
    product_code = data.get('product_code')
    quantity = data.get('quantity', 1)
    
    if not customer_user_id or not product_code:
        return jsonify({'error': 'customer_user_id and product_code are required'}), 400
    
    try:
        quantity = int(quantity)
        if quantity < 1:
            return jsonify({'error': 'quantity must be at least 1'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'quantity must be a valid integer'}), 400
    
    
    result = cart_service.add_to_cart(customer_user_id, product_code, quantity)
    return jsonify(result), 200 if result.get('success') else 400

@cart_bp.route('/update', methods=['PUT'])
def update_cart_item():
    """Update cart item quantity"""
    data = request.json
    if not data:
        return jsonify({'error': 'JSON data is required'}), 400
    
    customer_user_id = data.get('customer_user_id')
    product_code = data.get('product_code')
    quantity = data.get('quantity')
    
    if not customer_user_id or not product_code or quantity is None:
        return jsonify({'error': 'customer_user_id, product_code, and quantity are required'}), 400
    
    try:
        quantity = int(quantity)
        if quantity < 0:
            return jsonify({'error': 'quantity cannot be negative'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'quantity must be a valid integer'}), 400
    
    if quantity == 0:
        # Remove item if quantity is 0
        result = cart_service.remove_cart_item(customer_user_id, product_code)
    else:
        result = cart_service.update_cart_item(customer_user_id, product_code, quantity)
    
    return jsonify(result), 200 if result.get('success') else 400

@cart_bp.route('/item', methods=['DELETE'])
def remove_cart_item():
    """Remove specific item from cart"""
    data = request.json
    if not data:
        return jsonify({'error': 'JSON data is required'}), 400
    
    customer_user_id = data.get('customer_user_id')
    product_code = data.get('product_code')
    
    if not customer_user_id or not product_code:
        return jsonify({'error': 'customer_user_id and product_code are required'}), 400
    
    result = cart_service.remove_cart_item(customer_user_id, product_code)
    return jsonify(result), 200 if result.get('success') else 400

@cart_bp.route('/clear', methods=['DELETE'])
def clear_cart():
    """Clear entire cart"""
    data = request.json
    if not data:
        return jsonify({'error': 'JSON data is required'}), 400
    
    customer_user_id = data.get('user_id')
    if not customer_user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    result = cart_service.clear_cart(customer_user_id)
    return jsonify(result), 200 if result.get('success') else 400

@cart_bp.route('/save', methods=['POST'])
def save_cart():
    """Save entire cart (legacy endpoint)"""
    data = request.json
    if not data:
        return jsonify({'error': 'JSON data is required'}), 400
    
    customer_user_id = data.get('customer_user_id')
    items = data.get('items', [])
    
    if not customer_user_id:
        return jsonify({'error': 'customer_user_id is required'}), 400
    
    result = cart_service.save_cart(customer_user_id, items)
    return jsonify(result), 200 if result.get('success') else 400