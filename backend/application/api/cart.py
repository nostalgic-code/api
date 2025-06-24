from flask import Blueprint, request, jsonify
from application.services.cart_service import CartService

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')
cart_service = CartService()

@cart_bp.route('/', methods=['GET'])
def get_cart():
    user_id = int(request.args.get('user_id'))
    cart = cart_service.get_cart(user_id)
    return jsonify(cart or {}), 200

@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data['user_id']
    product_code = data['product_code']
    quantity = data.get('quantity', 1)
    cart = cart_service.add_to_cart(user_id, product_code, quantity)
    return jsonify(cart), 200

@cart_bp.route('/save', methods=['POST'])
def save_cart():
    data = request.json
    user_id = data['user_id']
    items = data['items']
    cart = cart_service.save_cart(user_id, items)
    return jsonify(cart), 200