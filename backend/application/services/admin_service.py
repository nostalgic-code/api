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
from application.services.helpers import user_helpers, customer_helpers


class AdminService:
    """Centralized service for platform administration tasks"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    ################################################################################## USER MANAGEMENT METHODS ##################################################################################
    
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
            query = user_helpers.apply_user_filters(query, filters)
            
            # Apply sorting
            sort_field = filters.get('sort', '-created_at')
            query = user_helpers.apply_sorting(query, CustomerUser, sort_field)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            page = pagination.get('page', 1)
            limit = min(pagination.get('limit', 20), 100)  # Cap at 100
            offset = (page - 1) * limit
            
            users = query.offset(offset).limit(limit).all()
            
            # Format response
            result = {
                'data': [user_helpers.format_user_response(user) for user in users],
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
            user_data = user_helpers.format_user_response(user)
            
            # Add detailed information
            user_data['details'] = {
                'permission_code_details': user_helpers.get_permission_code_details(user.permission_code) if user.permission_code else None,
                'depot_names': user_helpers.get_depot_names(user.depot_access) if user.depot_access else [],
                'activity_summary': user_helpers.get_user_activity_summary(user_id),
                'approval_info': user_helpers.get_approval_info(user) if user.status != CustomerUserStatus.PENDING else None,
                'approval_eligibility_details': user_helpers.format_approval_eligibility(user.approval_eligibility) if user.approval_eligibility else None
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
                - permission_code: str (optional for approve)
                - force_approve: bool (optional for approve)
                
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
                return user_helpers.approve_user_action(user, context)
            else:
                return user_helpers.reject_user_action(user, context)
                
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error performing {action} on user {user_id}: {str(e)}")
            raise

    def update_user(self, user_id: int, updates: Dict) -> Dict:
        """
        Update user attributes (role, permission_code, depot_access)
        
        Args:
            user_id: ID of the user
            updates: Dict containing fields to update:
                - role: str
                - permission_code: str
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
                result = user_helpers.update_user_role(user, updates['role'])
                if result:
                    updated_fields.append('role')
            
            # Update permission_code if provided (this will also update permissions)
            if 'permission_code' in updates:
                result = user_helpers.update_permission_code(user, updates['permission_code'])
                if not result['success']:
                    return result
                updated_fields.append('permission_code')
                updated_fields.append('permissions')
            
            # Update depot access if provided
            if 'depot_access' in updates:
                validation_result = user_helpers.validate_depot_access(updates['depot_access'])
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
                'user': user_helpers.format_user_response(user)
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating user {user_id}: {str(e)}")
            raise
    
    ################################################################################ CUSTOMER MANAGEMENT METHODS ################################################################################
    
    def get_customers(self, filters: Dict[str, Any], pagination: Dict[str, int]) -> Dict:
        """
        Get customers with comprehensive filtering and user statistics
        
        Args:
            filters: Dict containing:
                - status: str or list (pending, approved, rejected, on_hold)
                - type: str or list (standard, premium, enterprise)
                - search: str (searches name, code, account_number)
                - created_after: str (ISO date)
                - created_before: str (ISO date)
                - has_pending_users: bool
                - sort: str (field to sort by, prefix with - for desc)
            pagination: Dict containing:
                - page: int (default 1)
                - limit: int (default 20, max 100)
                
        Returns:
            Dict containing:
                - data: List of customer objects with user stats
                - meta: Pagination and filter metadata
        """
        try:
            query = Customer.query
            
            # Apply filters
            query = customer_helpers.apply_customer_filters(query, filters)
            
            # Apply sorting
            sort_field = filters.get('sort', '-created_at')
            query = customer_helpers.apply_sorting(query, Customer, sort_field)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            page = pagination.get('page', 1)
            limit = min(pagination.get('limit', 20), 100)
            offset = (page - 1) * limit
            
            customers = query.offset(offset).limit(limit).all()
            
            # Format response with stats
            result = {
                'data': [customer_helpers.format_customer_response(customer) for customer in customers],
                'meta': {
                    'total': total_count,
                    'page': page,
                    'limit': limit,
                    'pages': (total_count + limit - 1) // limit,
                    'filters_applied': {k: v for k, v in filters.items() if v is not None}
                }
            }
            
            self.logger.info(f"Found {total_count} customers with filters: {filters}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching customers: {str(e)}")
            raise
    
    def get_customer_details(self, customer_id: int) -> Dict:
        """
        Get detailed customer information including all users, stats, and history
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            Dict with comprehensive customer information
        """
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found")
            
            # Get detailed information
            customer_data = customer_helpers.get_customer_details(customer)
            
            self.logger.info(f"Retrieved details for customer {customer.name}")
            return customer_data
            
        except Exception as e:
            self.logger.error(f"Error fetching customer details for ID {customer_id}: {str(e)}")
            raise
    
    def update_customer(self, customer_id: int, updates: Dict) -> Dict:
        """
        Update customer attributes (mainly status)
        
        Args:
            customer_id: ID of the customer
            updates: Dict containing fields to update:
                - status: str (approved, on_hold, etc)
                - updated_by: int (ID of platform user)
                - reason: str (optional reason for status change)
                
        Returns:
            Dict with updated customer information
        """
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found',
                    'code': 'CUSTOMER_NOT_FOUND'
                }
            
            updated_fields = []
            
            # Update status if provided
            if 'status' in updates:
                # Validate status change
                validation = customer_helpers.validate_customer_status_change(
                    customer, updates['status']
                )
                if not validation['valid']:
                    return {
                        'success': False,
                        'error': validation['error'],
                        'code': 'INVALID_STATUS_CHANGE'
                    }
                
                old_status = customer.status
                new_status_enum = CustomerStatus[updates['status'].upper()]
                customer.status = new_status_enum
                updated_fields.append('status')
                
                # Log the status change
                self.logger.info(
                    f"Customer {customer.name} status changed from {old_status.value} "
                    f"to {new_status_enum.value} by platform user {updates.get('updated_by')}. "
                    f"Reason: {updates.get('reason', 'Not provided')}"
                )
                
                # Handle side effects of status changes
                if new_status_enum == CustomerStatus.ON_HOLD:
                    # When putting customer on hold, could optionally deactivate all users
                    # This is a business decision - implement if needed
                    pass
            
            customer.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Customer updated successfully',
                'updated_fields': updated_fields,
                'customer': customer_helpers.format_customer_response(customer)
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating customer {customer_id}: {str(e)}")
            raise
    
    def get_customer_users(self, customer_id: int, filters: Dict) -> Dict:
        """
        Get all users for a specific customer with filtering
        
        Args:
            customer_id: ID of the customer
            filters: Dict containing user filters and pagination
            
        Returns:
            Dict with filtered user list for the customer
        """
        try:
            # Verify customer exists
            customer = Customer.query.get(customer_id)
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found")
            
            # Add customer_id to filters
            filters['customer_id'] = customer_id
            
            # Use existing get_users method with customer filter
            pagination = {
                'page': filters.pop('page', 1),
                'limit': filters.pop('limit', 20)
            }
            
            result = self.get_users(filters, pagination)
            
            # Add customer info to response
            result['customer'] = {
                'id': customer.id,
                'name': customer.name,
                'code': customer.customer_code,
                'status': customer.status.value
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching users for customer {customer_id}: {str(e)}")
            raise
    

    ################################################################################  DASHBOARD METHODS ################################################################################
    
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
                },
                'permission_codes': {
                    'total': PermissionCode.query.count()
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error fetching system stats: {str(e)}")
            raise

    ################################################################################  DEPRECATED METHODS ################################################################################
    
    # Keep existing get_all_customers method for backward compatibility
    # Mark as deprecated in documentation
    def get_all_customers(self, filter_by: Optional[Dict] = None) -> List[Dict]:
        """
        DEPRECATED: Use get_customers() instead.
        Get all customers with optional filtering.
        """
        filters = filter_by or {}
        pagination = {'page': 1, 'limit': 1000}  # Get all
        result = self.get_customers(filters, pagination)
        return result['data']
    
    # Keep existing update_customer_status for backward compatibility
    def update_customer_status(self, customer_id: int, new_status: str, 
                              updated_by: int, reason: Optional[str] = None) -> Dict:
        """
        DEPRECATED: Use update_customer() instead.
        Update customer status.
        """
        return self.update_customer(customer_id, {
            'status': new_status,
            'updated_by': updated_by,
            'reason': reason
        })
    
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
    
# Create singleton instance
admin_service = AdminService()