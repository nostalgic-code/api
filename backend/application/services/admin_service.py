"""
Admin Service Module

Handles all platform administration tasks including user approval,
customer management, and role assignments.

This service is exclusively for platform users and centralizes
all administrative business logic.

Key Features:
- User approval/rejection workflows
- Customer management
- Role and permission assignments
- System monitoring and reporting

Author: Development Team
Version: 1.0
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Query
from datetime import datetime
from sqlalchemy import or_

from application import db
from application.models.customer import Customer, CustomerStatus
from application.models.customer_user import CustomerUser, CustomerUserStatus, CustomerUserRole
from application.models.platform_user import PlatformUser
from application.models.permission_code import PermissionCode
from application.models.depot import Depot


class AdminService:
    """Centralized service for platform administration tasks"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # User Management Methods - Refactored
    
    def get_users(self, filters: Dict[str, Any], pagination: Dict[str, int]) -> Dict:
        """
        Unified method to get users with comprehensive filtering
        
        Args:
            filters: Dict containing:
                - status: str or list (pending, approved, rejected)
                - customer_id: int or list
                - role: str or list (owner, staff, viewer)
                - search: str (searches name, email)
                - created_after: datetime
                - created_before: datetime
                - sort: str (field to sort by, prefix with - for desc)
            pagination: Dict containing:
                - page: int (default 1)
                - limit: int (default 20, max 100)
                
        Returns:
            Dict containing:
                - data: List of user objects
                - meta: Pagination and filter metadata
        """
        try:
            query = CustomerUser.query
            
            # Apply filters
            query = self._apply_user_filters(query, filters)
            
            # Apply sorting
            sort_field = filters.get('sort', '-created_at')
            query = self._apply_sorting(query, CustomerUser, sort_field)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            page = pagination.get('page', 1)
            limit = min(pagination.get('limit', 20), 100)  # Cap at 100
            offset = (page - 1) * limit
            
            users = query.offset(offset).limit(limit).all()
            
            # Format response
            result = {
                'data': [self._format_user_response(user) for user in users],
                'meta': {
                    'total': total_count,
                    'page': page,
                    'limit': limit,
                    'pages': (total_count + limit - 1) // limit,
                    'filters_applied': {k: v for k, v in filters.items() if v is not None}
                }
            }
            
            self.logger.info(f"Found {total_count} users with filters: {filters}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching users: {str(e)}")
            raise
    
    def get_user_details(self, user_id: int) -> Dict:
        """
        Get detailed user information including permissions, depot access, activity history
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict with comprehensive user information
        """
        try:
            user = CustomerUser.query.get(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            # Get basic user info
            user_data = self._format_user_response(user)
            
            # Add detailed information
            user_data['details'] = {
                'permission_code_details': self._get_permission_code_details(user.permission_code) if user.permission_code else None,
                'depot_names': self._get_depot_names(user.depot_access) if user.depot_access else [],
                'activity_summary': self._get_user_activity_summary(user_id),
                'approval_info': self._get_approval_info(user) if user.status != CustomerUserStatus.PENDING else None
            }
            
            return user_data
            
        except Exception as e:
            self.logger.error(f"Error fetching user details for ID {user_id}: {str(e)}")
            raise
    
    def perform_user_action(self, user_id: int, action: str, context: Dict) -> Dict:
        """
        Handle approve/reject actions with context
        
        Args:
            user_id: ID of the user
            action: 'approve' or 'reject'
            context: Dict containing:
                - actor_id: ID of platform user performing action
                - reason: str (required for reject)
                - depot_access: list (optional for approve)
                - custom_permissions: dict (optional for approve)
                
        Returns:
            Dict with action result
        """
        try:
            if action not in ['approve', 'reject']:
                raise ValueError(f"Invalid action: {action}")
            
            user = CustomerUser.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }
            
            if user.status != CustomerUserStatus.PENDING:
                return {
                    'success': False,
                    'error': f'User status is {user.status.value}, not pending',
                    'code': 'INVALID_STATUS'
                }
            
            if action == 'approve':
                return self._approve_user_action(user, context)
            else:
                return self._reject_user_action(user, context)
                
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error performing {action} on user {user_id}: {str(e)}")
            raise
    
    def update_user(self, user_id: int, updates: Dict) -> Dict:
        """
        Update user attributes (role, permissions, depot_access)
        
        Args:
            user_id: ID of the user
            updates: Dict containing fields to update:
                - role: str
                - permissions: dict
                - depot_access: list
                - updated_by: int (ID of platform user)
                
        Returns:
            Dict with updated user information
        """
        try:
            user = CustomerUser.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }
            
            updated_fields = []
            
            # Update role if provided
            if 'role' in updates:
                result = self._update_user_role(user, updates['role'])
                if result:
                    updated_fields.append('role')
            
            # Update permissions if provided
            if 'permissions' in updates:
                user.permissions = updates['permissions']
                updated_fields.append('permissions')
            
            # Update depot access if provided
            if 'depot_access' in updates:
                validation_result = self._validate_depot_access(updates['depot_access'])
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'error': validation_result['error'],
                        'code': 'INVALID_DEPOTS'
                    }
                user.depot_access = updates['depot_access']
                updated_fields.append('depot_access')
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            self.logger.info(
                f"User {user.email} updated by platform user {updates.get('updated_by')}. "
                f"Fields updated: {', '.join(updated_fields)}"
            )
            
            return {
                'success': True,
                'message': 'User updated successfully',
                'updated_fields': updated_fields,
                'user': self._format_user_response(user)
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating user {user_id}: {str(e)}")
            raise
    
    # Helper Methods
    
    def _apply_user_filters(self, query: Query, filters: Dict) -> Query:
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
    
    def _apply_sorting(self, query: Query, model, sort_field: str) -> Query:
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
    
    def _format_user_response(self, user: CustomerUser) -> Dict:
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
            'permission_code': user.permission_code
        }
    
    def _approve_user_action(self, user: CustomerUser, context: Dict) -> Dict:
        """Handle user approval"""
        # Validate depot access if provided
        if context.get('depot_access'):
            validation_result = self._validate_depot_access(context['depot_access'])
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'code': 'INVALID_DEPOTS'
                }
        
        # Update user
        user.status = CustomerUserStatus.APPROVED
        user.updated_at = datetime.utcnow()
        
        if context.get('depot_access') is not None:
            user.depot_access = context['depot_access']
        
        if context.get('custom_permissions') is not None:
            user.permissions = context['custom_permissions']
        
        db.session.commit()
        
        self.logger.info(
            f"User {user.email} approved by platform user {context['actor_id']}"
        )
        
        # TODO: Send approval notification email
        
        return {
            'success': True,
            'message': f'User {user.email} approved successfully',
            'user': self._format_user_response(user)
        }
    
    def _reject_user_action(self, user: CustomerUser, context: Dict) -> Dict:
        """Handle user rejection"""
        if not context.get('reason'):
            return {
                'success': False,
                'error': 'Rejection reason is required',
                'code': 'REASON_REQUIRED'
            }
        
        user.status = CustomerUserStatus.REJECTED
        user.updated_at = datetime.utcnow()
        
        # TODO: Store rejection reason in audit log or user table
        
        db.session.commit()
        
        self.logger.info(
            f"User {user.email} rejected by platform user {context['actor_id']}. "
            f"Reason: {context['reason']}"
        )
        
        # TODO: Send rejection notification email
        
        return {
            'success': True,
            'message': f'User {user.email} rejected',
            'reason': context['reason'],
            'user': self._format_user_response(user)
        }
    
    def _update_user_role(self, user: CustomerUser, new_role: str) -> bool:
        """Update user role and associated permission code"""
        try:
            new_role_enum = CustomerUserRole[new_role.upper()]
        except KeyError:
            raise ValueError(f'Invalid role: {new_role}')
        
        old_role = user.role
        user.role = new_role_enum
        
        # Update permission code to match new role
        permission_code = PermissionCode.query.filter_by(
            role=new_role_enum.value
        ).first()
        
        if permission_code:
            user.permission_code = permission_code.code
        
        return True
    
    def _validate_depot_access(self, depot_codes: List[str]) -> Dict:
        """Validate depot codes exist"""
        valid_depots = {d.code for d in Depot.query.all()}
        invalid_depots = set(depot_codes) - valid_depots
        
        if invalid_depots:
            return {
                'valid': False,
                'error': f'Invalid depot codes: {", ".join(invalid_depots)}'
            }
        
        return {'valid': True}
    
    def _get_permission_code_details(self, code: str) -> Optional[Dict]:
        """Get permission code details"""
        if not code:
            return None
            
        perm_code = PermissionCode.query.filter_by(code=code).first()
        if not perm_code:
            return None
            
        return {
            'code': perm_code.code,
            'role': perm_code.role,
            'permissions': perm_code.permissions
        }
    
    def _get_depot_names(self, depot_codes: List[str]) -> List[Dict]:
        """Get depot names for codes"""
        if not depot_codes:
            return []
            
        depots = Depot.query.filter(Depot.code.in_(depot_codes)).all()
        return [{'code': d.code, 'name': d.name} for d in depots]
    
    def _get_user_activity_summary(self, user_id: int) -> Dict:
        """Get user activity summary"""
        # TODO: Implement when activity tracking is added
        return {
            'last_login': None,
            'total_logins': 0,
            'last_action': None
        }
    
    def _get_approval_info(self, user: CustomerUser) -> Optional[Dict]:
        """Get approval/rejection information"""
        # TODO: Implement when approval tracking fields are added to model
        return {
            'approved_at': user.updated_at.isoformat() if user.status == CustomerUserStatus.APPROVED else None,
            'approved_by': None,  # Will be populated when fields are added
            'rejected_at': user.updated_at.isoformat() if user.status == CustomerUserStatus.REJECTED else None,
            'rejected_by': None,  # Will be populated when fields are added
            'rejection_reason': None  # Will be populated when fields are added
        }
    
    
    
    
    
    
    
    
    
    
    ################################################################################ CUSTOMER MANAGEMENT METHODS ################################################################################
    
    def get_all_customers(self, filter_by: Optional[Dict] = None) -> List[Dict]:
        """
        Get all customers with optional filtering.
        
        Args:
            filter_by: Optional filters (status, type, search)
            
        Returns:
            List of customers with statistics
        """
        try:
            query = Customer.query
            
            # Apply filters
            if filter_by:
                if filter_by.get('status'):
                    query = query.filter_by(status=CustomerStatus[filter_by['status'].upper()])
                if filter_by.get('type'):
                    query = query.filter_by(type=filter_by['type'])
                if filter_by.get('search'):
                    search = f"%{filter_by['search']}%"
                    query = query.filter(
                        or_(
                            Customer.name.ilike(search),
                            Customer.customer_code.ilike(search)
                        )
                    )
            
            customers = query.order_by(Customer.name).all()
            
            result = []
            for customer in customers:
                # Get user statistics
                user_stats = db.session.query(
                    CustomerUser.status, db.func.count(CustomerUser.id)
                ).filter_by(customer_id=customer.id).group_by(CustomerUser.status).all()
                
                user_counts = {
                    'total': sum(count for _, count in user_stats),
                    'approved': 0,
                    'pending': 0,
                    'rejected': 0
                }
                
                for status, count in user_stats:
                    user_counts[status.value] = count
                
                result.append({
                    'id': customer.id,
                    'code': customer.customer_code,
                    'account_number': customer.account_number,
                    'name': customer.name,
                    'type': customer.type.value,
                    'status': customer.status.value,
                    'users': user_counts,
                    'created_at': customer.created_at.isoformat() if customer.created_at else None
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching customers: {str(e)}")
            raise
    
    def update_customer_status(self, customer_id: int, new_status: str, 
                              updated_by: int, reason: Optional[str] = None) -> Dict:
        """
        Update customer status (approve, suspend, etc).
        
        Args:
            customer_id: ID of customer to update
            new_status: New status value
            updated_by: ID of platform user making change
            reason: Optional reason for status change
            
        Returns:
            Result dictionary
        """
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found',
                    'code': 'CUSTOMER_NOT_FOUND'
                }
            
            # Validate status
            try:
                new_status_enum = CustomerStatus[new_status.upper()]
            except KeyError:
                return {
                    'success': False,
                    'error': f'Invalid status: {new_status}',
                    'code': 'INVALID_STATUS'
                }
            
            old_status = customer.status
            customer.status = new_status_enum
            customer.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            self.logger.info(
                f"Customer {customer.name} status changed from {old_status.value} "
                f"to {new_status} by platform user {updated_by}"
            )
            
            # If suspending customer, optionally suspend all users
            if new_status_enum == CustomerStatus.ON_HOLD:
                # This will trigger the login validation to fail for all users
                pass
            
            return {
                'success': True,
                'message': f'Customer status updated to {new_status}',
                'customer': {
                    'id': customer.id,
                    'name': customer.name,
                    'old_status': old_status.value,
                    'new_status': new_status
                }
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating customer {customer_id}: {str(e)}")
            raise
    
    # Role and Permission Management
    
    def assign_role(self, user_id: int, new_role: str, assigned_by: int) -> Dict:
        """
        Change a user's role.
        
        Args:
            user_id: ID of user to update
            new_role: New role (owner, staff, viewer)
            assigned_by: ID of platform user making change
            
        Returns:
            Result dictionary
        """
        try:
            user = CustomerUser.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }
            
            # Validate role
            try:
                new_role_enum = CustomerUserRole[new_role.upper()]
            except KeyError:
                return {
                    'success': False,
                    'error': f'Invalid role: {new_role}',
                    'code': 'INVALID_ROLE'
                }
            
            old_role = user.role
            user.role = new_role_enum
            
            # Update permission code to match new role
            permission_code = PermissionCode.query.filter_by(
                role=new_role_enum.value
            ).first()
            
            if permission_code:
                user.permission_code = permission_code.code
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            self.logger.info(
                f"User {user.email} role changed from {old_role.value} "
                f"to {new_role} by platform user {assigned_by}"
            )
            
            return {
                'success': True,
                'message': f'User role updated to {new_role}',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'old_role': old_role.value,
                    'new_role': new_role,
                    'permission_code': user.permission_code
                }
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error assigning role to user {user_id}: {str(e)}")
            raise
    
    def update_user_permissions(self, user_id: int, permissions: Dict, 
                               updated_by: int) -> Dict:
        """
        Update a user's custom permissions.
        
        Args:
            user_id: ID of user to update
            permissions: New permissions object
            updated_by: ID of platform user making change
            
        Returns:
            Result dictionary
        """
        try:
            user = CustomerUser.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }
            
            user.permissions = permissions
            user.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            self.logger.info(
                f"User {user.email} permissions updated by platform user {updated_by}"
            )
            
            return {
                'success': True,
                'message': 'User permissions updated',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'permissions': user.permissions
                }
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating permissions for user {user_id}: {str(e)}")
            raise
    
    # System Information Methods
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """
        Get recent admin activity for dashboard.
        
        Args:
            limit: Number of recent activities to return
            
        Returns:
            List of recent admin activities
        """
        try:
            # For now, we'll get recent user approvals/rejections and customer status changes
            # This is a simplified version - in production you'd have a dedicated audit log table
            
            activities = []
            
            # Get recently approved users
            recent_approved = CustomerUser.query.filter_by(
                status=CustomerUserStatus.APPROVED
            ).order_by(CustomerUser.updated_at.desc()).limit(5).all()
            
            for user in recent_approved:
                if user.updated_at:
                    activities.append({
                        'id': f"user_approved_{user.id}",
                        'type': 'user_approved',
                        'message': f"User {user.email} was approved",
                        'timestamp': user.updated_at.isoformat(),
                        'user_email': user.email,
                        'customer_name': user.customer.name if user.customer else None
                    })
            
            # Get recently rejected users
            recent_rejected = CustomerUser.query.filter_by(
                status=CustomerUserStatus.REJECTED
            ).order_by(CustomerUser.updated_at.desc()).limit(5).all()
            
            for user in recent_rejected:
                if user.updated_at:
                    activities.append({
                        'id': f"user_rejected_{user.id}",
                        'type': 'user_rejected',
                        'message': f"User {user.email} was rejected",
                        'timestamp': user.updated_at.isoformat(),
                        'user_email': user.email,
                        'customer_name': user.customer.name if user.customer else None
                    })
            
            # Get recently updated customers
            recent_customers = Customer.query.order_by(
                Customer.updated_at.desc()
            ).limit(3).all()
            
            for customer in recent_customers:
                if customer.updated_at and customer.updated_at != customer.created_at:
                    activities.append({
                        'id': f"customer_updated_{customer.id}",
                        'type': 'customer_updated',
                        'message': f"Customer {customer.name} status was updated",
                        'timestamp': customer.updated_at.isoformat(),
                        'customer_name': customer.name,
                        'customer_status': customer.status.value
                    })
            
            # Sort by timestamp and limit
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            return activities[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching recent activity: {str(e)}")
            return []
    
    def get_system_stats(self) -> Dict:
        """
        Get system-wide statistics for dashboard.
        
        Returns:
            Dictionary of system statistics
        """
        try:
            stats = {
                'customers': {
                    'total': Customer.query.count(),
                    'approved': Customer.query.filter_by(status=CustomerStatus.APPROVED).count(),
                    'pending': Customer.query.filter_by(status=CustomerStatus.PENDING).count(),
                    'suspended': Customer.query.filter_by(status=CustomerStatus.ON_HOLD).count()
                },
                'users': {
                    'customer_users': {
                        'total': CustomerUser.query.count(),
                        'approved': CustomerUser.query.filter_by(status=CustomerUserStatus.APPROVED).count(),
                        'pending': CustomerUser.query.filter_by(status=CustomerUserStatus.PENDING).count(),
                        'rejected': CustomerUser.query.filter_by(status=CustomerUserStatus.REJECTED).count()
                    },
                    'platform_users': {
                        'total': PlatformUser.query.count(),
                        'admins': PlatformUser.query.filter_by(role='admin').count()
                    }
                },
                'depots': {
                    'total': Depot.query.count()
                    # Removed the 'active' filter since the field doesn't exist
                },
                'permission_codes': {
                    'total': PermissionCode.query.count()
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error fetching system stats: {str(e)}")
            raise


# Create singleton instance
admin_service = AdminService()