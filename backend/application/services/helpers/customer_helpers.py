"""
Customer Helper Functions

Utility functions for customer-related operations including filtering,
formatting, and validation.

Author: Development Team
Version: 1.0
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Query
from sqlalchemy import column, or_, and_, func, table
from datetime import datetime

from application.models.customer import Customer, CustomerStatus, CustomerType
from application.models.customer_user import CustomerUser, CustomerUserStatus
from application.models.depot import Depot

logger = logging.getLogger(__name__)


def apply_customer_filters(query: Query, filters: Dict[str, Any]) -> Query:
    """
    Apply filters to customer query
    
    Args:
        query: Base SQLAlchemy query
        filters: Dict containing filter parameters
        
    Returns:
        Modified query with filters applied
    """
    # Status filter (supports multiple values)
    if filters.get('status'):
        statuses = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
        status_enums = []
        for status in statuses:
            try:
                status_enums.append(CustomerStatus[status.upper()])
            except KeyError:
                logger.warning(f"Invalid customer status filter: {status}")
        if status_enums:
            query = query.filter(Customer.status.in_(status_enums))
    
    # Type filter (supports multiple values)
    if filters.get('type'):
        types = filters['type'] if isinstance(filters['type'], list) else [filters['type']]
        type_enums = []
        for ctype in types:
            try:
                type_enums.append(CustomerType[ctype.upper()])
            except KeyError:
                logger.warning(f"Invalid customer type filter: {ctype}")
        if type_enums:
            query = query.filter(Customer.type.in_(type_enums))
    
    # Search filter (searches name, code, account number)
    if filters.get('search'):
        search = f"%{filters['search']}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search),
                Customer.customer_code.ilike(search),
                Customer.account_number.ilike(search)
            )
        )
    
    # Date filters
    if filters.get('created_after'):
        try:
            date = datetime.fromisoformat(filters['created_after'].replace('Z', '+00:00'))
            query = query.filter(Customer.created_at >= date)
        except:
            logger.warning(f"Invalid created_after date: {filters['created_after']}")
    
    if filters.get('created_before'):
        try:
            date = datetime.fromisoformat(filters['created_before'].replace('Z', '+00:00'))
            query = query.filter(Customer.created_at <= date)
        except:
            logger.warning(f"Invalid created_before date: {filters['created_before']}")
    
    # Has pending users filter
    if filters.get('has_pending_users'):
        if filters['has_pending_users'] in ['true', True, '1', 1]:
            # Subquery to find customers with pending users
            query = query.filter(
                Customer.id.in_(
                    CustomerUser.query
                    .filter_by(status=CustomerUserStatus.PENDING)
                    .with_entities(CustomerUser.customer_id)
                    .distinct()
                )
            )
    
    return query


def apply_sorting(query: Query, model, sort_field: str) -> Query:
    """
    Apply sorting to query
    
    Args:
        query: SQLAlchemy query
        model: Model class to sort
        sort_field: Field to sort by (prefix with - for desc)
        
    Returns:
        Modified query with sorting applied
    """
    if sort_field.startswith('-'):
        field_name = sort_field[1:]
        order = 'desc'
    else:
        field_name = sort_field
        order = 'asc'
    
    # Map common sort fields
    sort_mapping = {
        'name': Customer.name,
        'code': Customer.customer_code,
        'created_at': Customer.created_at,
        'updated_at': Customer.updated_at,
        'status': Customer.status
    }
    
    if field_name in sort_mapping:
        field = sort_mapping[field_name]
        query = query.order_by(field.desc() if order == 'desc' else field.asc())
    elif hasattr(model, field_name):
        field = getattr(model, field_name)
        query = query.order_by(field.desc() if order == 'desc' else field.asc())
    
    return query


def format_customer_response(customer: Customer, include_stats: bool = True) -> Dict:
    """
    Format customer object for API response
    
    Args:
        customer: Customer model instance
        include_stats: Whether to include user statistics
        
    Returns:
        Formatted customer dictionary
    """
    response = {
        'id': customer.id,
        'code': customer.customer_code,
        'account_number': customer.account_number,
        'name': customer.name,
        'type': customer.type.value if customer.type else None,
        'status': customer.status.value if customer.status else None,
        'created_at': customer.created_at.isoformat() if customer.created_at else None,
        'updated_at': customer.updated_at.isoformat() if customer.updated_at else None
    }
    
    if include_stats:
        response['user_stats'] = get_customer_user_stats(customer.id)
    
    return response


def get_customer_user_stats(customer_id: int) -> Dict[str, int]:
    """
    Get user statistics for a customer
    
    Args:
        customer_id: ID of the customer
        
    Returns:
        Dict with user counts by status
    """
    from application import db
    
    # Get user counts by status using modern SQLAlchemy syntax
    users = CustomerUser.query.filter_by(customer_id=customer_id).all()
    
    stats = {
        'total': 0,
        'approved': 0,
        'pending': 0,
        'rejected': 0
    }
    
    # Count users by status
    for user in users:
        stats['total'] += 1
        if user.status:
            status_key = user.status.value.lower()
            if status_key in stats:
                stats[status_key] += 1
    
    return stats


def get_customer_details(customer: Customer) -> Dict:
    """
    Get comprehensive customer details
    
    Args:
        customer: Customer model instance
        
    Returns:
        Dict with detailed customer information
    """
    details = format_customer_response(customer, include_stats=True)
    
    # Add additional details
    details['details'] = {
        'user_breakdown': get_user_breakdown_by_role(customer.id),
        'depot_coverage': get_customer_depot_coverage(customer.id),
        'recent_activity': get_customer_recent_activity(customer.id),
        'owner_info': get_customer_owner_info(customer.id)
    }
    
    return details


def get_user_breakdown_by_role(customer_id: int) -> Dict:
    """
    Get user counts broken down by role and status
    
    Args:
        customer_id: ID of the customer
        
    Returns:
        Dict with user counts by role and status
    """
    from application import db
    from application.models.customer_user import CustomerUserRole
    
    users = CustomerUser.query.filter_by(customer_id=customer_id).all()
    
    breakdown = {
        'owner': {'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0},
        'staff': {'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0},
        'viewer': {'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0}
    }
    
    for user in users:
        role_key = user.role.value if user.role else 'viewer'
        status_key = user.status.value if user.status else 'pending'
        
        if role_key in breakdown:
            breakdown[role_key]['total'] += 1
            if status_key in breakdown[role_key]:
                breakdown[role_key][status_key] += 1
    
    return breakdown


def get_customer_depot_coverage(customer_id: int) -> List[Dict]:
    """
    Get depots that customer users have access to
    
    Args:
        customer_id: ID of the customer
        
    Returns:
        List of depot information with user counts
    """
    from application import db
    
    # Get all unique depot codes from customer users
    users = CustomerUser.query.filter_by(
        customer_id=customer_id,
        status=CustomerUserStatus.APPROVED
    ).filter(
        CustomerUser.depot_access.isnot(None)
    ).all()
    
    depot_user_count = {}
    all_depot_codes = set()
    
    for user in users:
        if user.depot_access:
            for depot_code in user.depot_access:
                all_depot_codes.add(depot_code)
                depot_user_count[depot_code] = depot_user_count.get(depot_code, 0) + 1
    
    # Get depot details
    depots = Depot.query.filter(Depot.code.in_(all_depot_codes)).all() if all_depot_codes else []
    
    return [
        {
            'code': depot.code,
            'name': depot.name,
            'user_count': depot_user_count.get(depot.code, 0)
        }
        for depot in depots
    ]


def get_customer_recent_activity(customer_id: int, limit: int = 5) -> List[Dict]:
    """
    Get recent activity for a customer
    
    Args:
        customer_id: ID of the customer
        limit: Number of activities to return
        
    Returns:
        List of recent activities
    """
    # For now, return recent user status changes
    # In production, this would query an audit log table
    recent_users = CustomerUser.query.filter_by(
        customer_id=customer_id
    ).filter(
        CustomerUser.updated_at.isnot(None)
    ).order_by(
        CustomerUser.updated_at.desc()
    ).limit(limit).all()
    
    activities = []
    for user in recent_users:
        if user.updated_at != user.created_at:
            activities.append({
                'type': 'user_status_change',
                'message': f"User {user.email} status changed to {user.status.value}",
                'timestamp': user.updated_at.isoformat(),
                'user_email': user.email
            })
    
    return activities


def get_customer_owner_info(customer_id: int) -> Optional[Dict]:
    """
    Get information about the customer's owner(s)
    
    Args:
        customer_id: ID of the customer
        
    Returns:
        Dict with owner information or None
    """
    from application.models.customer_user import CustomerUserRole
    
    owner = CustomerUser.query.filter_by(
        customer_id=customer_id,
        role=CustomerUserRole.OWNER,
        status=CustomerUserStatus.APPROVED
    ).first()
    
    if owner:
        return {
            'id': owner.id,
            'name': owner.name,
            'email': owner.email,
            'phone': owner.phone,
            'approved_at': owner.updated_at.isoformat() if owner.updated_at else None
        }
    
    return None


def validate_customer_status_change(customer: Customer, new_status: str) -> Dict:
    """
    Validate if a customer status change is allowed
    
    Args:
        customer: Customer instance
        new_status: Proposed new status
        
    Returns:
        Dict with 'valid' bool and optional 'error' message
    """
    try:
        new_status_enum = CustomerStatus[new_status.upper()]
    except KeyError:
        return {
            'valid': False,
            'error': f'Invalid status: {new_status}'
        }
    
    current_status = customer.status
    
    # Define allowed transitions
    allowed_transitions = {
        CustomerStatus.PENDING: [CustomerStatus.APPROVED, CustomerStatus.REJECTED],
        CustomerStatus.APPROVED: [CustomerStatus.ON_HOLD],
        CustomerStatus.ON_HOLD: [CustomerStatus.APPROVED],
        CustomerStatus.REJECTED: [CustomerStatus.PENDING]  # Allow resubmission
    }
    
    if current_status in allowed_transitions:
        if new_status_enum not in allowed_transitions[current_status]:
            return {
                'valid': False,
                'error': f'Cannot change status from {current_status.value} to {new_status}'
            }
    
    return {'valid': True}


def get_customer_summary(customer: Customer) -> Dict:
    """
    Get a brief summary of customer for listings
    
    Args:
        customer: Customer instance
        
    Returns:
        Dict with summary information
    """
    stats = get_customer_user_stats(customer.id)
    
    return {
        'id': customer.id,
        'code': customer.customer_code,
        'name': customer.name,
        'status': customer.status.value if customer.status else None,
        'type': customer.type.value if customer.type else None,
        'user_counts': {
            'total': stats['total'],
            'active': stats['approved'],
            'pending': stats['pending']
        },
        'created_at': customer.created_at.isoformat() if customer.created_at else None
    }