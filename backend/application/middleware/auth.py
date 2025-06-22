"""
Authentication and Authorization Middleware

This module provides decorators for securing API endpoints with token-based
authentication and role/permission-based authorization.

Key Features:
- Token-based authentication for both CustomerUser and PlatformUser
- Permission-based authorization with effective permissions calculation
- Request context enrichment with user information

Author: Development Team
Version: 1.0
"""

from functools import wraps
from flask import request, jsonify, g
from datetime import datetime
import logging

from backend.application.models.user_session import UserSession
from backend.application.models.customer_user import CustomerUser, CustomerUserStatus
from backend.application.models.permission_code import PermissionCode

logger = logging.getLogger(__name__)


def token_required(f):
    """
    Decorator to validate session token and attach user to request context.
    
    This decorator:
    1. Extracts token from Authorization header
    2. Validates the token against active sessions
    3. Fetches the corresponding user (CustomerUser or PlatformUser)
    4. Attaches user and user_type to Flask's g object
    5. Rejects invalid/expired tokens with 401
    
    Usage:
        @app.route('/api/protected')
        @token_required
        def protected_route():
            user = g.current_user
            user_type = g.user_type
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                # Expected format: "Bearer <token>"
                parts = auth_header.split()
                if parts[0].lower() == 'bearer' and len(parts) == 2:
                    token = parts[1]
            except Exception:
                pass
        
        if not token:
            return jsonify({
                'error': 'Authentication token is missing',
                'code': 'TOKEN_MISSING'
            }), 401
        
        try:
            # Find active session
            session = UserSession.query.filter(
                UserSession.session_token == token,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                return jsonify({
                    'error': 'Invalid or expired token',
                    'code': 'TOKEN_INVALID'
                }), 401
            
            # Get the user based on user_type
            user = session.user  # Uses the polymorphic property
            
            if not user:
                return jsonify({
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 401
            
            # Additional validation for customer users
            if session.user_type == 'customer_user':
                if user.status != CustomerUserStatus.APPROVED:
                    return jsonify({
                        'error': 'User account is not approved',
                        'code': 'USER_NOT_APPROVED'
                    }), 401
                
                if user.customer.status.value != 'approved':
                    return jsonify({
                        'error': 'Customer account is not active',
                        'code': 'CUSTOMER_NOT_ACTIVE'
                    }), 401
            
            # Attach user and type to request context
            g.current_user = user
            g.user_type = session.user_type
            g.session = session
            
            # Calculate effective permissions for customer users
            if session.user_type == 'customer_user':
                g.effective_permissions = _calculate_effective_permissions(user)
            else:
                # Platform users have implicit full permissions
                g.effective_permissions = None
            
            logger.info(f"Authenticated {session.user_type}: {user.email}")
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in token validation: {str(e)}")
            return jsonify({
                'error': 'Authentication failed',
                'code': 'AUTH_ERROR'
            }), 401
    
    return decorated_function


def permission_required(resource, action):
    """
    Decorator to check if user has specific permission.
    
    This decorator:
    1. Runs after @token_required
    2. Checks if user has permission for resource.action
    3. Platform users bypass all permission checks
    4. Returns 403 if permission is missing
    
    Args:
        resource (str): Resource name (e.g., 'orders', 'quotes', 'users')
        action (str): Action name (e.g., 'create', 'read', 'update', 'delete')
    
    Usage:
        @app.route('/api/orders', methods=['POST'])
        @token_required
        @permission_required('orders', 'create')
        def create_order():
            # Only users with orders.create permission can access
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Ensure token_required has run first
            if not hasattr(g, 'current_user'):
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # Platform users have all permissions
            if g.user_type == 'platform_user':
                return f(*args, **kwargs)
            
            # Check customer user permissions
            if g.user_type == 'customer_user':
                permissions = g.effective_permissions or {}
                
                # Check if resource exists in permissions
                if resource not in permissions:
                    logger.warning(
                        f"Permission denied for {g.current_user.email}: "
                        f"No access to resource '{resource}'"
                    )
                    return jsonify({
                        'error': 'Permission denied',
                        'code': 'PERMISSION_DENIED',
                        'resource': resource
                    }), 403
                
                # Check if action is allowed
                resource_perms = permissions.get(resource, {})
                if not resource_perms.get(action, False):
                    logger.warning(
                        f"Permission denied for {g.current_user.email}: "
                        f"No '{action}' permission on '{resource}'"
                    )
                    return jsonify({
                        'error': 'Permission denied',
                        'code': 'PERMISSION_DENIED',
                        'resource': resource,
                        'action': action
                    }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def platform_user_required(f):
    """
    Decorator to ensure only platform users can access an endpoint.
    
    This decorator:
    1. Must be used after @token_required
    2. Checks if the authenticated user is a PlatformUser
    3. Rejects CustomerUsers with 403
    
    Usage:
        @app.route('/api/admin/users')
        @token_required
        @platform_user_required
        def admin_users():
            # Only platform users can access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ensure token_required has run first
        if not hasattr(g, 'current_user'):
            return jsonify({
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401
        
        if g.user_type != 'platform_user':
            logger.warning(
                f"Platform access denied for customer user: {g.current_user.email}"
            )
            return jsonify({
                'error': 'Access denied. Platform users only.',
                'code': 'PLATFORM_USERS_ONLY'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def customer_user_required(f):
    """
    Decorator to ensure only customer users can access an endpoint.
    
    This decorator:
    1. Must be used after @token_required
    2. Checks if the authenticated user is a CustomerUser
    3. Rejects PlatformUsers with 403
    
    Usage:
        @app.route('/api/my-orders')
        @token_required
        @customer_user_required
        def my_orders():
            # Only customer users can access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ensure token_required has run first
        if not hasattr(g, 'current_user'):
            return jsonify({
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401
        
        if g.user_type != 'customer_user':
            logger.warning(
                f"Customer access denied for platform user: {g.current_user.email}"
            )
            return jsonify({
                'error': 'Access denied. Customer users only.',
                'code': 'CUSTOMER_USERS_ONLY'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def _calculate_effective_permissions(user: CustomerUser) -> dict:
    """
    Calculate effective permissions by merging default and custom permissions.
    
    Args:
        user: CustomerUser instance
        
    Returns:
        dict: Merged permissions object
    """
    permissions = {}
    
    # Start with permission code defaults if available
    if user.permission_code:
        permission_code = PermissionCode.query.get(user.permission_code)
        if permission_code and permission_code.default_permissions:
            permissions = permission_code.default_permissions.copy()
    
    # Override with custom permissions
    if user.permissions:
        for key, value in user.permissions.items():
            if isinstance(value, dict) and key in permissions:
                # Merge nested permissions
                permissions[key].update(value)
            else:
                # Override completely
                permissions[key] = value
    
    return permissions


# Utility functions for common permission checks
def has_permission(resource: str, action: str) -> bool:
    """
    Check if current user has a specific permission.
    
    Args:
        resource: Resource name
        action: Action name
        
    Returns:
        bool: True if user has permission
    """
    if not hasattr(g, 'current_user'):
        return False
    
    if g.user_type == 'platform_user':
        return True
    
    permissions = g.effective_permissions or {}
    return permissions.get(resource, {}).get(action, False)


def get_current_user():
    """Get the current authenticated user or None."""
    return getattr(g, 'current_user', None)


def get_user_type():
    """Get the current user type or None."""
    return getattr(g, 'user_type', None)


def get_effective_permissions():
    """Get the current user's effective permissions or None."""
    return getattr(g, 'effective_permissions', None)