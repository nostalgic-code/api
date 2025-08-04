"""
Sales Order API Module

Endpoints related to sales order processing and submission to external systems.

Key Features:
- Sales order creation
- Order processing
- External API integration
- Order history retrieval

Author: Development Team
Version: 1.1
"""

from flask import Blueprint, request, jsonify, g
import logging
from datetime import datetime
import requests
import json

from application.middleware.auth import token_required, customer_user_required
from application import db
from application.models.order import Order, OrderItem, OrderStatus
from application.services.api_client import ApiClient

# Create Blueprint for sales order routes
sales_order_bp = Blueprint('sales_order', __name__, url_prefix='/sales-order')
logger = logging.getLogger(__name__)
api_client = ApiClient()

@sales_order_bp.route('/submit', methods=['POST'])
@token_required
@customer_user_required
def submit_sales_order():
    """
    Submit a sales order to the external supplier system
    
    Request Body:
        JSON object with sales order payload
    
    Returns:
        Submission status and P-number if successful
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON'
            }), 400
        
        # Get data from request
        data = request.get_json()
        
        if 'payload' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required payload field'
            }), 400
        
        payload = data['payload']
        
        # Validate required fields
        required_fields = [
            'branch', 'customer.account.no', 'order.id', 'order.key', 
            'order.status', 'order.total', 'items'
        ]
        
        for field in required_fields:
            if field not in payload:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Validate items
        if not isinstance(payload['items'], list) or not payload['items']:
            return jsonify({
                'success': False,
                'message': 'Order must contain at least one item'
            }), 400
        
        # Log the order details
        logger.info(f"Submitting sales order: {payload['order.id']}")
        logger.debug(f"Order payload: {json.dumps(payload)}")
        
        # Call the ERP API to submit the sales order
        erp_response = api_client.call_erp_api('getResources/subroutine/postSalesOrderV2', payload)
        
        if not erp_response.get('success'):
            logger.error(f"ERP API error: {erp_response.get('message')}")
            
            # Save failed order for reference
            user = g.current_user
            
            # Create order record with failed status
            order = Order.query.filter_by(order_number=payload['order.id']).first()
            
            if not order:
                order = Order(
                    customer_id=user.customer_id,
                    customer_user_id=user.id,
                    order_number=payload['order.id'],
                    status=OrderStatus.ERROR,
                    total_amount=float(payload['order.total']),
                    vat_amount=float(payload['order.vat']) if 'order.vat' in payload else 0.0,
                    external_reference=payload['order.key']
                )
                db.session.add(order)
                db.session.commit()
            
            return jsonify({
                'success': False,
                'message': f"Failed to submit order to ERP system: {erp_response.get('message', 'Unknown error')}"
            }), 400
        
        # Get the P-number from the response
        p_number = erp_response.get('data', {}).get('p_number')
        
        if not p_number:
            logger.warning("P-number not found in ERP response, generating a placeholder")
            # Fallback if p_number is not in response
            p_number = f"P{datetime.now().strftime('%Y%m%d')}-{payload['order.id'][-6:]}"
        
        # Save order details to database for reference
        user = g.current_user
        
        # Create or update order record
        order = Order.query.filter_by(order_number=payload['order.id']).first()
        
        if not order:
            order = Order(
                customer_id=user.customer_id,
                customer_user_id=user.id,
                order_number=payload['order.id'],
                p_number=p_number,
                status=OrderStatus.SUBMITTED,
                total_amount=float(payload['order.total']),
                vat_amount=float(payload['order.vat']) if 'order.vat' in payload else 0.0,
                external_reference=payload['order.key']
            )
            db.session.add(order)
        else:
            order.p_number = p_number
            order.status = OrderStatus.SUBMITTED
            order.external_reference = payload['order.key']
        
        # Save order items
        for item_data in payload['items']:
            item = OrderItem(
                order=order,
                product_code=item_data['sku.no'],
                product_name=item_data['sku.desc'],
                quantity=int(item_data['sku.qty']),
                price=float(item_data['sku.price.excl']),
                vat=float(item_data['sku.vat']) if 'sku.vat' in item_data else 0.0
            )
            db.session.add(item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Sales order submitted successfully',
            'data': {
                'order_id': payload['order.id'],
                'p_number': p_number
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting sales order: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@sales_order_bp.route('/history', methods=['GET'])
@token_required
@customer_user_required
def get_sales_order_history():
    """
    Get sales order history for the current customer user
    
    Returns:
        JSON with list of orders and their details
    """
    try:
        user = g.current_user
        
        # Get all orders for this user
        orders = Order.query.filter_by(
            customer_user_id=user.id
        ).order_by(Order.created_at.desc()).all()
        
        result = []
        for order in orders:
            # Get order items
            items = OrderItem.query.filter_by(order_id=order.id).all()
            
            # Format order data
            order_data = {
                'id': str(order.id),
                'order_number': order.order_number,
                'p_number': order.p_number,
                'status': order.status.value,
                'total_amount': float(order.total_amount),
                'vat_amount': float(order.vat_amount) if order.vat_amount else 0.0,
                'order_date': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'external_reference': order.external_reference,
                'items': [
                    {
                        'product_code': item.product_code,
                        'product_name': item.product_name,
                        'quantity': item.quantity,
                        'price': float(item.price),
                        'vat': float(item.vat) if item.vat else 0.0
                    } for item in items
                ]
            }
            
            result.append(order_data)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error fetching sales order history: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500
