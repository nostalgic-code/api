"""
User Helper Functions

Contains utility functions for user management operations including
filtering, formatting, validation, and user actions.

Author: Development Team
Version: 1.0
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Query
from datetime import datetime
from sqlalchemy import or_

from application import db
from application.models.customer_user import CustomerUser, CustomerUserStatus, CustomerUserRole
from application.models.permission_code import PermissionCode
from application.models.depot import Depot

logger = logging.getLogger(__name__)


def apply_user_filters(query: Query, filters: Dict) -> Query:
    """Apply filters to user query"""
    
    # Status filter (supports multiple values)
    if filters.get('status'):
        statuses = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
        status_enums = []
        for status in statuses:
            if status == 'pending':
                status_enums.append(CustomerUserStatus.PENDING)
            elif status == 'approved':
                status_enums.append(CustomerUserStatus.APPROVED)
            elif status == 'rejected':
                status_enums.append(CustomerUserStatus.REJECTED)
        if status_enums:
            query = query.filter(CustomerUser.status.in_(status_enums))
    
    # Customer filter (supports multiple values)
    if filters.get('customer_id'):
        customer_ids = filters['customer_id'] if isinstance(filters['customer_id'], list) else [filters['customer_id']]
        query = query.filter(CustomerUser.customer_id.in_(customer_ids))
    
    # Role filter (supports multiple values)
    if filters.get('role'):
        roles = filters['role'] if isinstance(filters['role'], list) else [filters['role']]
        role_enums = [CustomerUserRole[role.upper()] for role in roles]
        query = query.filter(CustomerUser.role.in_(role_enums))
    
    # Search filter
    if filters.get('search'):
        search = f"%{filters['search']}%"
        query = query.filter(
            or_(
                CustomerUser.name.ilike(search),
                CustomerUser.email.ilike(search)
            )
        )
    
    # Date filters
    if filters.get('created_after'):
        query = query.filter(CustomerUser.created_at >= filters['created_after'])
    if filters.get('created_before'):
        query = query.filter(CustomerUser.created_at <= filters['created_before'])
    
    return query


def format_approval_eligibility(eligibility: Dict) -> Dict:
    """Format approval eligibility for display"""
    if not eligibility:
        return None

    return {
        'status': eligibility.get('status', 'UNKNOWN'),
        'validation_date': eligibility.get('validation_date'),
        'mismatches': eligibility.get('mismatches', []),
        'warnings': eligibility.get('warnings', []),
        'approved_at': eligibility.get('approved_at'),
        'approved_with_status': eligibility.get('approved_with_status'),
        'approved_by': eligibility.get('approved_by')
    }


def apply_sorting(query: Query, model, sort_field: str) -> Query:
    """Apply sorting to query"""
    if sort_field.startswith('-'):
        field_name = sort_field[1:]
        order = 'desc'
    else:
        field_name = sort_field
        order = 'asc'
    
    if hasattr(model, field_name):
        field = getattr(model, field_name)
        query = query.order_by(field.desc() if order == 'desc' else field.asc())
    
    return query


def format_user_response(user: CustomerUser) -> Dict:
    """Format user object for API response"""
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
        'role': user.role.value,
        'status': user.status.value,
        'customer': {
            'id': user.customer.id,
            'name': user.customer.name,
            'code': user.customer.customer_code,
            'status': user.customer.status.value
        } if user.customer else None,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'days_pending': (datetime.utcnow() - user.created_at).days if user.created_at and user.status == CustomerUserStatus.PENDING else None,
        'depot_access': user.depot_access,
        'permissions': user.permissions,
        'permission_code': user.permission_code,
        'approval_eligibility': user.approval_eligibility
    }


def approve_user_action(user: CustomerUser, context: Dict) -> Dict:
    """Handle user approval"""
    # Check approval eligibility unless force_approve is True
    force_approve = context.get('force_approve', False)
    
    if not force_approve and user.approval_eligibility:
        eligibility_status = user.approval_eligibility.get('status', 'UNKNOWN')
        if eligibility_status == 'INELIGIBLE':
            return {
                'success': False,
                'error': 'User is not eligible for approval. Review the validation issues.',
                'code': 'NOT_ELIGIBLE',
                'approval_eligibility': user.approval_eligibility
            }
        elif eligibility_status == 'REQUIRES_REVIEW':
            # Include warning but allow approval
            logger.warning(
                f"Approving user {user.email} with validation mismatches: "
                f"{user.approval_eligibility.get('mismatches', [])}"
            )
    
    # Ensure user has a valid customer_id
    if not user.customer_id:
        return {
            'success': False,
            'error': 'User does not have a valid customer association',
            'code': 'NO_CUSTOMER_ASSOCIATION'
        }
    
    # Validate depot access if provided
    if context.get('depot_access'):
        validation_result = validate_depot_access(context['depot_access'])
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['error'],
                'code': 'INVALID_DEPOTS'
            }
    
    # Determine permission code
    permission_code = context.get('permission_code')
    if not permission_code:
        # Get default permission code for the role
        default_permission = PermissionCode.query.filter_by(
            role=user.role.value
        ).first()
        permission_code = default_permission.code if default_permission else 'VIEWER'
    
    # Update permission code and permissions
    result = update_permission_code(user, permission_code)
    if not result['success']:
        return result
    
    # Update user status and other fields
    user.status = CustomerUserStatus.APPROVED
    user.updated_at = datetime.utcnow()
    
    if context.get('depot_access') is not None:
        user.depot_access = context['depot_access']
    
    # Update approval eligibility with approval details
    if user.approval_eligibility:
        user.approval_eligibility['approved_at'] = datetime.utcnow().isoformat()
        user.approval_eligibility['approved_with_status'] = user.approval_eligibility.get('status', 'UNKNOWN') if not force_approve else 'FORCE_APPROVED'
        user.approval_eligibility['approved_by'] = context.get('actor_id')
    
    db.session.commit()
    
    logger.info(
        f"User {user.email} approved by platform user {context['actor_id']} "
        f"with permission code {permission_code}"
    )
    
    # TODO: Send approval notification email
    
    return {
        'success': True,
        'message': f'User {user.email} approved successfully',
        'user': format_user_response(user)
    }


def reject_user_action(user: CustomerUser, context: Dict) -> Dict:
    """Handle user rejection"""
    if not context.get('reason'):
        return {
            'success': False,
            'error': 'Rejection reason is required',
            'code': 'REASON_REQUIRED'
        }
    
    user.status = CustomerUserStatus.REJECTED
    user.updated_at = datetime.utcnow()

    # Update approval eligibility with rejection details
    if user.approval_eligibility:
        user.approval_eligibility['rejected_at'] = datetime.utcnow().isoformat()
        user.approval_eligibility['rejected_by'] = context.get('actor_id')
        user.approval_eligibility['rejection_reason'] = context.get('reason')
    
    # TODO: Store rejection reason in audit log or user table
    
    db.session.commit()
    
    logger.info(
        f"User {user.email} rejected by platform user {context['actor_id']}. "
        f"Reason: {context['reason']}"
    )
    
    # TODO: Send rejection notification email
    
    return {
        'success': True,
        'message': f'User {user.email} rejected',
        'reason': context['reason'],
        'user': format_user_response(user)
    }


def update_user_role(user: CustomerUser, new_role: str) -> bool:
    """Update user role and associated permission code"""
    try:
        new_role_enum = CustomerUserRole[new_role.upper()]
    except KeyError:
        raise ValueError(f'Invalid role: {new_role}')
    
    old_role = user.role
    user.role = new_role_enum
    
    return True


def validate_depot_access(depot_codes: List[str]) -> Dict:
    """Validate depot codes exist"""
    valid_depots = {d.code for d in Depot.query.all()}
    invalid_depots = set(depot_codes) - valid_depots
    
    if invalid_depots:
        return {
            'valid': False,
            'error': f'Invalid depot codes: {", ".join(invalid_depots)}'
        }
    
    return {'valid': True}


def get_permission_code_details(code: str) -> Optional[Dict]:
    """Get permission code details"""
    if not code:
        return None
        
    perm_code = PermissionCode.query.filter_by(code=code).first()
    if not perm_code:
        return None
        
    return {
        'code': perm_code.code,
        'role': perm_code.role.value if hasattr(perm_code.role, 'value') else perm_code.role,
        'permissions': perm_code.default_permissions
    }


def get_depot_names(depot_codes: List[str]) -> List[Dict]:
    """Get depot names for codes"""
    if not depot_codes:
        return []
        
    depots = Depot.query.filter(Depot.code.in_(depot_codes)).all()
    return [{'code': d.code, 'name': d.name} for d in depots]


def get_user_activity_summary(user_id: int) -> Dict:
    """Get user activity summary"""
    # TODO: Implement when activity tracking is added
    return {
        'last_login': None,
        'total_logins': 0,
        'last_action': None
    }


def get_approval_info(user: CustomerUser) -> Optional[Dict]:
    """Get approval/rejection information"""
    # TODO: Implement when approval tracking fields are added to model
    return {
        'approved_at': user.updated_at.isoformat() if user.status == CustomerUserStatus.APPROVED else None,
        'approved_by': None,  # Will be populated when fields are added
        'rejected_at': user.updated_at.isoformat() if user.status == CustomerUserStatus.REJECTED else None,
        'rejected_by': None,  # Will be populated when fields are added
        'rejection_reason': None  # Will be populated when fields are added
    }


def update_permission_code(user: CustomerUser, permission_code: str) -> Dict:
    """
    Update user's permission code and automatically update permissions

    Args:
        user: CustomerUser instance
        permission_code: New permission code
    
    Returns:
        Dict with success status
    """
    # Get the permission code object - must be exact match
    permission_obj = PermissionCode.query.filter_by(code=permission_code).first()
    if not permission_obj:
        return {
            'success': False,
            'error': f'Invalid permission code: {permission_code}',
            'code': 'INVALID_PERMISSION_CODE'
        }

    # Verify the permission code is appropriate for the user's role
    if permission_obj.role != user.role.value:
        return {
            'success': False,
            'error': f'Permission code {permission_code} does not match user role {user.role.value}',
            'code': 'ROLE_MISMATCH'
        }

    # Set the permission code
    user.permission_code = permission_code

    # Update permissions from the permission code's default_permissions
    if permission_obj.default_permissions:
        user.permissions = permission_obj.default_permissions.copy()
    else:
        user.permissions = {}

    logger.info(
        f"Updated user {user.email} permission_code to {permission_code} "
        f"with permissions: {user.permissions}"
    )

    return {'success': True}
