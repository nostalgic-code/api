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


# User Management Endpoints

@admin_bp.route('/pending-users', methods=['GET'])
@token_required
@platform_user_required
def get_pending_users():
    """
    Get all pending customer users.
    
    Query Parameters:
        - customer_id: Filter by customer
        - role: Filter by role (owner, staff, viewer)
        - created_after: ISO date string
        - search: Search by name or email
    
    Response:
        {
            "users": [...],
            "count": 1
        }
    """
    try:
        # Parse filters from query params
        filters = {}
        if request.args.get('customer_id'):
            filters['customer_id'] = int(request.args.get('customer_id'))
        if request.args.get('role'):
            filters['role'] = request.args.get('role')
        if request.args.get('created_after'):
            filters['created_after'] = request.args.get('created_after')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        pending_users = admin_service.get_users_by_status('pending', filter_by=filters)
        
        return jsonify({
            'users': pending_users,
            'count': len(pending_users)
        })
        
    except Exception as e:
        logger.error(f"Error in get_pending_users: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch pending users',
            'code': 'FETCH_ERROR'
        }), 500


@admin_bp.route('/active-users', methods=['GET'])
@token_required
@platform_user_required
def get_active_users():
    """
    Get all active (approved) customer users.
    
    Query Parameters:
        - customer_id: Filter by customer
        - role: Filter by role (owner, staff, viewer)
        - search: Search by name or email
    
    Response:
        {
            "users": [...],
            "count": 1
        }
    """
    try:
        # Parse filters from query params
        filters = {}
        if request.args.get('customer_id'):
            filters['customer_id'] = int(request.args.get('customer_id'))
        if request.args.get('role'):
            filters['role'] = request.args.get('role')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        active_users = admin_service.get_users_by_status('approved', filter_by=filters)
        
        return jsonify({
            'users': active_users,
            'count': len(active_users)
        })
        
    except Exception as e:
        logger.error(f"Error in get_active_users: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch active users',
            'code': 'FETCH_ERROR'
        }), 500


@admin_bp.route('/rejected-users', methods=['GET'])
@token_required
@platform_user_required
def get_rejected_users():
    """
    Get all rejected customer users.
    
    Query Parameters:
        - customer_id: Filter by customer
        - role: Filter by role (owner, staff, viewer)
        - search: Search by name or email
    
    Response:
        {
            "users": [...],
            "count": 1
        }
    """
    try:
        # Parse filters from query params
        filters = {}
        if request.args.get('customer_id'):
            filters['customer_id'] = int(request.args.get('customer_id'))
        if request.args.get('role'):
            filters['role'] = request.args.get('role')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        rejected_users = admin_service.get_users_by_status('rejected', filter_by=filters)
        
        return jsonify({
            'users': rejected_users,
            'count': len(rejected_users)
        })
        
    except Exception as e:
        logger.error(f"Error in get_rejected_users: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch rejected users',
            'code': 'FETCH_ERROR'
        }), 500


@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@token_required
@platform_user_required
def approve_user(user_id):
    """
    Approve a pending customer user.
    
    Request Body:
        {
            "depot_access": ["JHB", "CPT"],  // optional
            "custom_permissions": {           // optional
                "orders": {"create": true, "delete": false}
            }
        }
    
    Response:
        {
            "success": true,
            "message": "User john@company.com approved successfully",
            "user": {
                "id": 1,
                "email": "john@company.com",
                "status": "approved"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        result = admin_service.approve_user(
            user_id=user_id,
            approved_by=g.current_user.id,
            depot_access=data.get('depot_access'),
            custom_permissions=data.get('custom_permissions')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error approving user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to approve user',
            'code': 'APPROVAL_ERROR'
        }), 500


@admin_bp.route('/users/<int:user_id>/reject', methods=['POST'])
@token_required
@platform_user_required
def reject_user(user_id):
    """
    Reject a pending customer user.
    
    Request Body:
        {
            "reason": "Invalid company information"
        }
    
    Response:
        {
            "success": true,
            "message": "User john@company.com rejected",
            "reason": "Invalid company information"
        }
    """
    try:
        data = request.get_json()
        if not data or not data.get('reason'):
            return jsonify({
                'success': False,
                'error': 'Rejection reason is required',
                'code': 'REASON_REQUIRED'
            }), 400
        
        result = admin_service.reject_user(
            user_id=user_id,
            rejected_by=g.current_user.id,
            reason=data['reason']
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error rejecting user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to reject user',
            'code': 'REJECTION_ERROR'
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