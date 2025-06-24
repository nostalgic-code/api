from flask import Blueprint, request, jsonify
from application.services.CartService import CartService
from application.services import OrderService


order_bp = Blueprint('order', __name__, url_prefix='/orders')
order_service = OrderService()

@order_bp.route('/create', methods=['POST'])
def create_order():
    data = request.json
    user_id = data['user_id']
    order = order_service.create_order(user_id)
    return jsonify(order), 201

@order_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = order_service.get_order(order_id)
    if order:
        return jsonify(order), 200
    return jsonify({"error": "Order not found"}), 404