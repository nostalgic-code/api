"""
Admin API Module

Secure API endpoints for platform administration tasks.
All endpoints require platform user authentication.

Key Features:
- User approval/rejection workflows
- Customer management
- Role and permission assignments
- System monitoring

Author: Development Team
Version: 1.0
"""

from flask import Blueprint, request, jsonify, g
import logging

from application.middleware.auth import token_required, platform_user_required
from application.services.admin_service import admin_service


# Create Blueprint for admin routes
admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

@admin_bp.route('/users', methods=['GET'])
@token_required
@platform_user_required
def get_users():
    """
    Get all users with comprehensive filtering and pagination.
    
    Query Parameters:
        - status: Filter by status (comma-separated for multiple: pending,approved)
        - customer_id: Filter by customer (comma-separated for multiple)
        - role: Filter by role (comma-separated for multiple: owner,staff)
        - search: Search by name or email
        - created_after: ISO date string
        - created_before: ISO date string
        - sort: Sort field (prefix with - for desc: -created_at)
        - page: Page number (default: 1)
        - limit: Items per page (default: 20, max: 100)
    
    Response:
        {
            "data": [...],
            "meta": {
                "total": 100,
                "page": 1,
                "limit": 20,
                "pages": 5,
                "filters_applied": {...}
            }
        }
    """
    try:
        # Parse filters
        filters = {}
        
        # Handle multi-value parameters
        if request.args.get('status'):
            statuses = request.args.get('status').split(',')
            filters['status'] = statuses if len(statuses) > 1 else statuses[0]
        
        if request.args.get('customer_id'):
            customer_ids = request.args.get('customer_id').split(',')
            filters['customer_id'] = [int(id) for id in customer_ids]
        
        if request.args.get('role'):
            roles = request.args.get('role').split(',')
            filters['role'] = roles if len(roles) > 1 else roles[0]
        
        # Single value parameters
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        if request.args.get('created_after'):
            filters['created_after'] = request.args.get('created_after')
        
        if request.args.get('created_before'):
            filters['created_before'] = request.args.get('created_before')
        
        if request.args.get('sort'):
            filters['sort'] = request.args.get('sort')
        
        # Parse pagination
        pagination = {
            'page': int(request.args.get('page', 1)),
            'limit': int(request.args.get('limit', 20))
        }
        
        result = admin_service.get_users(filters=filters, pagination=pagination)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'code': 'INVALID_PARAMETER'
        }), 400
    except Exception as e:
        logger.error(f"Error in get_users: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch users',
            'code': 'FETCH_ERROR'
        }), 500


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
@platform_user_required
def get_user_details(user_id):
    """
    Get detailed information for a specific user.
    
    Response:
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@company.com",
            ...standard user fields...,
            "details": {
                "permission_code_details": {...},
                "depot_names": [...],
                "activity_summary": {...},
                "approval_info": {...}
            }
        }
    """
    try:
        user_details = admin_service.get_user_details(user_id)
        return jsonify(user_details), 200
        
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'code': 'USER_NOT_FOUND'
        }), 404
    except Exception as e:
        logger.error(f"Error fetching user details for ID {user_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch user details',
            'code': 'FETCH_ERROR'
        }), 500


@admin_bp.route('/users/<int:user_id>/actions', methods=['POST'])
@token_required
@platform_user_required
def perform_user_action(user_id):
    """
    Perform an action on a user (approve/reject).
    
    Request Body:
        {
            "action": "approve",  // or "reject"
            "reason": "Invalid information",  // required for reject
            "depot_access": ["JHB", "CPT"],  // optional for approve
            "permission_code": "ADMIN"  // optional for approve, defaults based on role
        }
    
    Response:
        {
            "success": true,
            "message": "User approved successfully",
            "user": {...}
        }
    """
    try:
        data = request.get_json()
        if not data or not data.get('action'):
            return jsonify({
                'error': 'Action is required',
                'code': 'ACTION_REQUIRED'
            }), 400
        
        action = data['action']
        context = {
            'actor_id': g.current_user.id,
            'reason': data.get('reason'),
            'depot_access': data.get('depot_access'),
            'custom_permissions': data.get('custom_permissions')
        }
        
        result = admin_service.perform_user_action(
            user_id=user_id,
            action=action,
            context=context
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error performing action on user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to perform action',
            'code': 'ACTION_ERROR'
        }), 500


@admin_bp.route('/users/<int:user_id>', methods=['PATCH'])
@token_required
@platform_user_required
def update_user(user_id):
    """
    Update user attributes.
    
    Request Body (all fields optional):
        {
            "role": "owner",
            "permission_code": "ADMIN",
            "depot_access": ["JHB", "CPT"]
        }
    
    Response:
        {
            "success": true,
            "message": "User updated successfully",
            "updated_fields": ["role", "permission_code", "permissions"],
            "user": {...}
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No update data provided',
                'code': 'NO_DATA'
            }), 400
        
        # Build updates dict with only provided fields
        updates = {
            'updated_by': g.current_user.id
        }
        
        if 'role' in data:
            updates['role'] = data['role']
        if 'permission_code' in data:
            updates['permission_code'] = data['permission_code']
        if 'depot_access' in data:
            updates['depot_access'] = data['depot_access']
        
        result = admin_service.update_user(
            user_id=user_id,
            updates=updates
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to update user',
            'code': 'UPDATE_ERROR'
        }), 500


# Customer Management Endpoints
@admin_bp.route('/customers', methods=['GET'])
@token_required
@platform_user_required
def get_customers():
    """
    Get all customers with comprehensive filtering and pagination.
    
    Query Parameters:
        - status: Filter by status (comma-separated for multiple: pending,approved,on_hold)
        - type: Filter by type (comma-separated for multiple: standard,premium)
        - search: Search by name, code, or account number
        - created_after: ISO date string
        - created_before: ISO date string
        - has_pending_users: Filter customers with pending users (true/false)
        - sort: Sort field (prefix with - for desc: -created_at)
        - page: Page number (default: 1)
        - limit: Items per page (default: 20, max: 100)
    
    Response:
        {
            "data": [
                {
                    "id": 1,
                    "code": "CUST001",
                    "name": "ABC Company",
                    "status": "approved",
                    "type": "enterprise",
                    "user_stats": {
                        "total": 10,
                        "approved": 7,
                        "pending": 2,
                        "rejected": 1
                    },
                    "created_at": "2025-06-01T..."
                }
            ],
            "meta": {
                "total": 50,
                "page": 1,
                "limit": 20,
                "pages": 3,
                "filters_applied": {...}
            }
        }
    """
    try:
        # Parse filters
        filters = {}
        
        # Handle multi-value parameters
        if request.args.get('status'):
            statuses = request.args.get('status').split(',')
            filters['status'] = statuses if len(statuses) > 1 else statuses[0]
        
        if request.args.get('type'):
            types = request.args.get('type').split(',')
            filters['type'] = types if len(types) > 1 else types[0]
        
        # Single value parameters
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        if request.args.get('created_after'):
            filters['created_after'] = request.args.get('created_after')
        
        if request.args.get('created_before'):
            filters['created_before'] = request.args.get('created_before')
        
        if request.args.get('has_pending_users'):
            filters['has_pending_users'] = request.args.get('has_pending_users')
        
        if request.args.get('sort'):
            filters['sort'] = request.args.get('sort')
        
        # Parse pagination
        pagination = {
            'page': int(request.args.get('page', 1)),
            'limit': int(request.args.get('limit', 20))
        }
        
        result = admin_service.get_customers(filters=filters, pagination=pagination)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'code': 'INVALID_PARAMETER'
        }), 400
    except Exception as e:
        logger.error(f"Error in get_customers: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch customers',
            'code': 'FETCH_ERROR'
        }), 500


@admin_bp.route('/customers/<int:customer_id>', methods=['GET'])
@token_required
@platform_user_required
def get_customer_details(customer_id):
    """
    Get detailed information for a specific customer.
    
    Response:
        {
            "id": 1,
            "code": "CUST001",
            "name": "ABC Company",
            "status": "approved",
            "type": "enterprise",
            "user_stats": {...},
            "details": {
                "user_breakdown": {
                    "owner": {"total": 1, "approved": 1, ...},
                    "staff": {"total": 5, "approved": 4, ...}
                },
                "depot_coverage": [
                    {"code": "JHB", "name": "Johannesburg", "user_count": 3}
                ],
                "recent_activity": [...],
                "owner_info": {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@abc.com"
                }
            }
        }
    """
    try:
        customer_details = admin_service.get_customer_details(customer_id)
        return jsonify(customer_details), 200
        
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'code': 'CUSTOMER_NOT_FOUND'
        }), 404
    except Exception as e:
        logger.error(f"Error fetching customer details for ID {customer_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch customer details',
            'code': 'FETCH_ERROR'
        }), 500


@admin_bp.route('/customers/<int:customer_id>', methods=['PATCH'])
@token_required
@platform_user_required
def update_customer(customer_id):
    """
    Update customer attributes.
    
    Request Body:
        {
            "status": "on_hold",
            "reason": "Non-payment"  // optional
        }
    
    Response:
        {
            "success": true,
            "message": "Customer updated successfully",
            "updated_fields": ["status"],
            "customer": {
                "id": 1,
                "code": "CUST001",
                "name": "ABC Company",
                "status": "on_hold",
                ...
            }
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No update data provided',
                'code': 'NO_DATA'
            }), 400
        
        # Build updates dict
        updates = {
            'updated_by': g.current_user.id
        }
        
        if 'status' in data:
            updates['status'] = data['status']
        if 'reason' in data:
            updates['reason'] = data['reason']
        
        result = admin_service.update_customer(
            customer_id=customer_id,
            updates=updates
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to update customer',
            'code': 'UPDATE_ERROR'
        }), 500


@admin_bp.route('/customers/<int:customer_id>/users', methods=['GET'])
@token_required
@platform_user_required
def get_customer_users(customer_id):
    """
    Get all users for a specific customer with filtering.
    
    Query Parameters:
        - status: Filter by user status (pending,approved,rejected)
        - role: Filter by user role (owner,staff,viewer)
        - search: Search by name or email
        - sort: Sort field (prefix with - for desc)
        - page: Page number (default: 1)
        - limit: Items per page (default: 20)
    
    Response:
        {
            "data": [...user list...],
            "meta": {
                "total": 10,
                "page": 1,
                "limit": 20,
                "pages": 1,
                "filters_applied": {...}
            },
            "customer": {
                "id": 1,
                "name": "ABC Company",
                "code": "CUST001",
                "status": "approved"
            }
        }
    """
    try:
        # Parse filters
        filters = {}
        
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        if request.args.get('role'):
            filters['role'] = request.args.get('role')
        
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        if request.args.get('sort'):
            filters['sort'] = request.args.get('sort')
        
        # Add pagination to filters (will be extracted in service)
        filters['page'] = int(request.args.get('page', 1))
        filters['limit'] = int(request.args.get('limit', 20))
        
        result = admin_service.get_customer_users(
            customer_id=customer_id,
            filters=filters
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'code': 'CUSTOMER_NOT_FOUND'
        }), 404
    except Exception as e:
        logger.error(f"Error fetching users for customer {customer_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch customer users',
            'code': 'FETCH_ERROR'
        }), 500

# Role and Permission Management

# @admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
# @token_required
# @platform_user_required
# def assign_user_role(user_id):
#     """
#     Change a user's role.
    
#     Request Body:
#         {
#             "role": "owner"
#         }
    
#     Response:
#         {
#             "success": true,
#             "message": "User role updated to owner",
#             "user": {
#                 "id": 1,
#                 "email": "john@company.com",
#                 "old_role": "staff",
#                 "new_role": "owner"
#             }
#         }
#     """
#     try:
#         data = request.get_json()
#         if not data or not data.get('role'):
#             return jsonify({
#                 'success': False,
#                 'error': 'Role is required',
#                 'code': 'ROLE_REQUIRED'
#             }), 400
        
#         result = admin_service.assign_role(
#             user_id=user_id,
#             new_role=data['role'],
#             assigned_by=g.current_user.id
#         )
        
#         if result['success']:
#             return jsonify(result), 200
#         else:
#             return jsonify(result), 400
            
#     except Exception as e:
#         logger.error(f"Error assigning role to user {user_id}: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': 'Failed to assign role',
#             'code': 'ROLE_ERROR'
#         }), 500


# @admin_bp.route('/users/<int:user_id>/permissions', methods=['PUT'])
# @token_required
# @platform_user_required
# def update_user_permissions(user_id):
#     """
#     Update user's custom permissions.
    
#     Request Body:
#         {
#             "permissions": {
#                 "orders": {"view": true, "create": true, "edit": false},
#                 "reports": {"view": true, "export": false}
#             }
#         }
    
#     Response:
#         {
#             "success": true,
#             "message": "User permissions updated",
#             "user": {
#                 "id": 1,
#                 "email": "john@company.com",
#                 "permissions": {...}
#             }
#         }
#     """
#     try:
#         data = request.get_json()
#         if not data or 'permissions' not in data:
#             return jsonify({
#                 'success': False,
#                 'error': 'Permissions object is required',
#                 'code': 'PERMISSIONS_REQUIRED'
#             }), 400
        
#         result = admin_service.update_user_permissions(
#             user_id=user_id,
#             permissions=data['permissions'],
#             updated_by=g.current_user.id
#         )
        
#         if result['success']:
#             return jsonify(result), 200
#         else:
#             return jsonify(result), 400
            
#     except Exception as e:
#         logger.error(f"Error updating permissions for user {user_id}: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': 'Failed to update permissions',
#             'code': 'PERMISSION_ERROR'
#         }), 500


# System Information

@admin_bp.route('/system/stats', methods=['GET'])
@token_required
@platform_user_required
def get_system_stats():
    """
    Get system-wide statistics.
    
    Response:
        {
            "customers": {
                "total": 50,
                "approved": 45,
                "pending": 3,
                "suspended": 2
            },
            "users": {
                "customer_users": {
                    "total": 250,
                    "approved": 200,
                    "pending": 30,
                    "rejected": 20
                },
                "platform_users": {
                    "total": 10,
                    "admins": 3
                }
            },
            "depots": {
                "total": 5,
                "active": 5
            }
        }
    """
    try:
        stats = admin_service.get_system_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error fetching system stats: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch system statistics',
            'code': 'STATS_ERROR'
        }), 500


@admin_bp.route('/system/recent-activity', methods=['GET'])
@token_required
@platform_user_required
def get_recent_activity():
    """
    Get recent admin activity for dashboard.
    
    Query Parameters:
        - limit: Number of activities to return (default: 10, max: 50)
    
    Response:
        {
            "activities": [
                {
                    "id": "user_approved_123",
                    "type": "user_approved",
                    "message": "User john@company.com was approved",
                    "timestamp": "2025-06-21T14:30:00",
                    "user_email": "john@company.com",
                    "customer_name": "ABC Company"
                }
            ],
            "count": 1
        }
    """
    try:
        limit = min(int(request.args.get('limit', 10)), 50)  # Cap at 50
        activities = admin_service.get_recent_activity(limit=limit)
        
        return jsonify({
            'activities': activities,
            'count': len(activities)
        })
        
    except Exception as e:
        logger.error(f"Error fetching recent activity: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch recent activity',
            'code': 'ACTIVITY_ERROR'
        }), 500


@admin_bp.route('/customers/upsert', methods=['POST'])
@token_required
@platform_user_required
def upsert_customer():
    """
    Create or update a customer record
    
    Request Body:
        {
            "customer_code": "999KJS02",
            "account_number": "999KJS02",
            "name": "KJ SPARES 4 U (PTY) LTD",
            "contact_one": "KASHIF",
            "telephone": "0725555888",
            "statement_email": "autozonehendrina@gmail.com",
            "branch_code": "999",
            "ship_via_code": "44",
            "assigned_rep": "17",
            "area_code": "009",
            "postal_address_line1": "57 KERK STREET",
            "postal_address_line2": "HENDRINA",
            "postal_address_line3": "1095",
            "street_address_line1": "27 VUYISILE MINI STREET",
            "street_address_line2": "BETHAL",
            "street_address_line3": "2310",
            "type": "company",
            "status": "on_hold",
            "created_at": "03-28-2024",
            "balance": "0.00",
            "credit_limit": "30000.00"
        }
    
    Response:
        {
            "success": true,
            "message": "Customer updated",
            "customer": {
                "id": 1,
                "customer_code": "999KJS02",
                "name": "KJ SPARES 4 U (PTY) LTD",
                "status": "on_hold"
            }
        }
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Request must be JSON'}), 400
        
        customer_data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_code', 'name']
        for field in required_fields:
            if field not in customer_data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        result = admin_service.upsert_customer(customer_data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in upsert_customer: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

