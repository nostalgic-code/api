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
        if 'permissions' in data:
            updates['permissions'] = data['permissions']
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
    Get all customers with statistics.
    
    Query Parameters:
        - status: Filter by status (approved, pending, suspended)
        - type: Filter by customer type
        - search: Search by name or code
    
    Response:
        {
            "customers": [
                {
                    "id": 1,
                    "code": "CUST001",
                    "name": "ABC Company",
                    "status": "approved",
                    "users": {
                        "total": 5,
                        "approved": 3,
                        "pending": 2
                    }
                }
            ],
            "count": 1
        }
    """
    try:
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('type'):
            filters['type'] = request.args.get('type')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        customers = admin_service.get_all_customers(filter_by=filters)
        
        return jsonify({
            'customers': customers,
            'count': len(customers)
        })
        
    except Exception as e:
        logger.error(f"Error fetching customers: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch customers',
            'code': 'FETCH_ERROR'
        }), 500


@admin_bp.route('/customers/<int:customer_id>/status', methods=['PUT'])
@token_required
@platform_user_required
def update_customer_status(customer_id):
    """
    Update customer status.
    
    Request Body:
        {
            "status": "suspended",
            "reason": "Non-payment"  // optional
        }
    
    Response:
        {
            "success": true,
            "message": "Customer status updated to suspended",
            "customer": {
                "id": 1,
                "name": "ABC Company",
                "old_status": "approved",
                "new_status": "suspended"
            }
        }
    """
    try:
        data = request.get_json()
        if not data or not data.get('status'):
            return jsonify({
                'success': False,
                'error': 'Status is required',
                'code': 'STATUS_REQUIRED'
            }), 400
        
        result = admin_service.update_customer_status(
            customer_id=customer_id,
            new_status=data['status'],
            updated_by=g.current_user.id,
            reason=data.get('reason')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update customer',
            'code': 'UPDATE_ERROR'
        }), 500


# Role and Permission Management

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@token_required
@platform_user_required
def assign_user_role(user_id):
    """
    Change a user's role.
    
    Request Body:
        {
            "role": "owner"
        }
    
    Response:
        {
            "success": true,
            "message": "User role updated to owner",
            "user": {
                "id": 1,
                "email": "john@company.com",
                "old_role": "staff",
                "new_role": "owner"
            }
        }
    """
    try:
        data = request.get_json()
        if not data or not data.get('role'):
            return jsonify({
                'success': False,
                'error': 'Role is required',
                'code': 'ROLE_REQUIRED'
            }), 400
        
        result = admin_service.assign_role(
            user_id=user_id,
            new_role=data['role'],
            assigned_by=g.current_user.id
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error assigning role to user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to assign role',
            'code': 'ROLE_ERROR'
        }), 500


@admin_bp.route('/users/<int:user_id>/permissions', methods=['PUT'])
@token_required
@platform_user_required
def update_user_permissions(user_id):
    """
    Update user's custom permissions.
    
    Request Body:
        {
            "permissions": {
                "orders": {"view": true, "create": true, "edit": false},
                "reports": {"view": true, "export": false}
            }
        }
    
    Response:
        {
            "success": true,
            "message": "User permissions updated",
            "user": {
                "id": 1,
                "email": "john@company.com",
                "permissions": {...}
            }
        }
    """
    try:
        data = request.get_json()
        if not data or 'permissions' not in data:
            return jsonify({
                'success': False,
                'error': 'Permissions object is required',
                'code': 'PERMISSIONS_REQUIRED'
            }), 400
        
        result = admin_service.update_user_permissions(
            user_id=user_id,
            permissions=data['permissions'],
            updated_by=g.current_user.id
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating permissions for user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update permissions',
            'code': 'PERMISSION_ERROR'
        }), 500


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


