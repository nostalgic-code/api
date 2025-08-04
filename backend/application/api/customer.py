"""
Customer API Module

Endpoints related to customer data management that are accessible to customer users.

Key Features:
- Customer profile management
- Customer data synchronization

Author: Development Team
Version: 1.0
"""

from flask import Blueprint, request, jsonify, g
import logging
from datetime import datetime

from application.middleware.auth import token_required, customer_user_required
from application.models.customer import Customer
from application import db

# Create Blueprint for customer routes
customer_bp = Blueprint('customer', __name__)
logger = logging.getLogger(__name__)

@customer_bp.route('/profile', methods=['GET'])
@token_required
@customer_user_required
def get_customer_profile():
    """
    Get current customer profile information
    
    Returns:
        Customer profile data
    """
    try:
        user = g.current_user
        customer = user.customer
        
        if not customer:
            return jsonify({
                'success': False,
                'message': 'Customer profile not found'
            }), 404
        
        customer_data = {
            'id': customer.id,
            'customer_code': customer.customer_code,
            'account_number': customer.account_number,
            'name': customer.name,
            'contact_one': customer.contact_one,
            'telephone': customer.telephone,
            'statement_email': customer.statement_email,
            'branch_code': customer.branch_code,
            'ship_via_code': customer.ship_via_code,
            'assigned_rep': customer.assigned_rep,
            'area_code': customer.area_code,
            'postal_address': {
                'line1': customer.postal_address_line1,
                'line2': customer.postal_address_line2,
                'line3': customer.postal_address_line3
            },
            'street_address': {
                'line1': customer.street_address_line1,
                'line2': customer.street_address_line2,
                'line3': customer.street_address_line3
            },
            'type': customer.type.value if hasattr(customer.type, 'value') else customer.type,
            'status': customer.status.value if hasattr(customer.status, 'value') else customer.status,
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
            'updated_at': customer.updated_at.isoformat() if customer.updated_at else None
        }
        
        return jsonify({
            'success': True,
            'customer': customer_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching customer profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@customer_bp.route('/update', methods=['POST'])
@token_required
@customer_user_required
def update_customer():
    """
    Update customer profile
    
    This endpoint allows customer users to update their customer record
    with data from external APIs or other sources.
    
    Request Body:
        JSON object with customer fields
    
    Returns:
        Updated customer data
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON'
            }), 400
        
        user = g.current_user
        customer = user.customer
        
        if not customer:
            return jsonify({
                'success': False,
                'message': 'Customer profile not found'
            }), 404
        
        # Get data from request
        data = request.get_json()
        
        # Fields that cannot be updated by customer users
        restricted_fields = ['id', 'customer_code', 'account_number', 'status', 'type']
        
        # Update customer fields
        for key, value in data.items():
            if key not in restricted_fields and hasattr(customer, key):
                setattr(customer, key, value)
        
        # Special handling for nested address fields
        if 'postal_address' in data and isinstance(data['postal_address'], dict):
            postal = data['postal_address']
            if 'line1' in postal:
                customer.postal_address_line1 = postal['line1']
            if 'line2' in postal:
                customer.postal_address_line2 = postal['line2']
            if 'line3' in postal:
                customer.postal_address_line3 = postal['line3']
                
        if 'street_address' in data and isinstance(data['street_address'], dict):
            street = data['street_address']
            if 'line1' in street:
                customer.street_address_line1 = street['line1']
            if 'line2' in street:
                customer.street_address_line2 = street['line2']
            if 'line3' in street:
                customer.street_address_line3 = street['line3']
        
        # Update timestamp
        customer.updated_at = datetime.utcnow()
        
        # Save changes
        db.session.commit()
        
        logger.info(f"Customer {customer.customer_code} updated by user {user.email}")
        
        return jsonify({
            'success': True,
            'message': 'Customer updated successfully',
            'customer': {
                'id': customer.id,
                'customer_code': customer.customer_code,
                'name': customer.name,
                'updated_at': customer.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating customer: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500
