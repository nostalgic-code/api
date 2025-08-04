from flask import Blueprint, request, jsonify, g
from application.services import OrderService
from application.middleware.auth import token_required, customer_user_required
from application.models.order import Order, OrderItem, OrderStatus
from application import db
import uuid
import json
import logging

order_bp = Blueprint('order', __name__, url_prefix='/orders')
order_service = OrderService()
logger = logging.getLogger(__name__)

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

@order_bp.route('/create', methods=['POST'])
@token_required
@customer_user_required
def create_customer_order():
    """Create a new order for a customer user"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        user = g.current_user
        
        # Validate required fields
        required_fields = ['customer_id', 'order_number', 'total_amount', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Create the order
        order = Order(
            id=uuid.uuid4(),
            user_id=str(user.id) if not isinstance(user.id, str) else user.id,
            customer_id=data['customer_id'],
            customer_user_id=user.id,
            order_number=data['order_number'],
            external_reference=data.get('order_key'),
            total_amount=data['total_amount'],
            vat_amount=data.get('vat_amount', 0.00),
            status=OrderStatus.PENDING
        )
        
        db.session.add(order)
        
        # Add order items
        items_data = data.get('items', [])
        if isinstance(items_data, str):
            items_data = json.loads(items_data)
            
        for item_data in items_data:
            item = OrderItem(
                id=uuid.uuid4(),
                order_id=order.id,
                product_code=item_data['product_code'],
                product_name=item_data.get('product_name'),
                quantity=item_data['quantity'],
                price=item_data['price'],
                vat=item_data.get('vat', 0.00)
            )
            db.session.add(item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'data': {
                'order_id': order.order_number
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating order: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500