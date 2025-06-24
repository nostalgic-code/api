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
from typing import Dict, List, Optional
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
    
    # User Management Methods
    
    def get_users_by_status(self, status: str, filter_by: Optional[Dict] = None) -> List[Dict]:
        """
        Get users by status with optional filtering.
        
        Args:
            status: User status (pending, approved, rejected)
            filter_by: Optional filters (customer_id, role, search, date_range)
            
        Returns:
            List of users with customer information
        """
        try:
            # Map status string to enum
            if status == 'pending':
                status_enum = CustomerUserStatus.PENDING
            elif status == 'approved':
                status_enum = CustomerUserStatus.APPROVED
            elif status == 'rejected':
                status_enum = CustomerUserStatus.REJECTED
            else:
                raise ValueError(f"Invalid status: {status}")
            
            query = CustomerUser.query.filter_by(status=status_enum)
            
            # Apply optional filters
            if filter_by:
                if filter_by.get('customer_id'):
                    query = query.filter_by(customer_id=filter_by['customer_id'])
                if filter_by.get('role'):
                    query = query.filter_by(role=CustomerUserRole[filter_by['role'].upper()])
                if filter_by.get('created_after'):
                    query = query.filter(CustomerUser.created_at >= filter_by['created_after'])
                if filter_by.get('search'):
                    search = f"%{filter_by['search']}%"
                    query = query.filter(
                        or_(
                            CustomerUser.name.ilike(search),
                            CustomerUser.email.ilike(search)
                        )
                    )
            
            users = query.order_by(CustomerUser.created_at.desc()).all()
            
            result = []
            for user in users:
                result.append({
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
                    },
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'days_pending': (datetime.utcnow() - user.created_at).days if user.created_at and status == 'pending' else None,
                    'depot_access': user.depot_access,
                    'permissions': user.permissions
                })
            
            self.logger.info(f"Found {len(result)} {status} users")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching {status} users: {str(e)}")
            raise
    
    def approve_user(self, user_id: int, approved_by: int, 
                    depot_access: Optional[List[str]] = None,
                    custom_permissions: Optional[Dict] = None) -> Dict:
        """
        Approve a pending customer user.
        
        Args:
            user_id: ID of user to approve
            approved_by: ID of platform user approving
            depot_access: Optional list of depot codes to assign
            custom_permissions: Optional custom permissions to set
            
        Returns:
            Result dictionary with success status
        """
        try:
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
            
            # Validate depot access if provided
            if depot_access:
                valid_depots = {d.code for d in Depot.query.all()}
                invalid_depots = set(depot_access) - valid_depots
                if invalid_depots:
                    return {
                        'success': False,
                        'error': f'Invalid depot codes: {", ".join(invalid_depots)}',
                        'code': 'INVALID_DEPOTS'
                    }
            
            # Update user
            user.status = CustomerUserStatus.APPROVED
            user.updated_at = datetime.utcnow()
            
            if depot_access is not None:
                user.depot_access = depot_access
            
            if custom_permissions is not None:
                user.permissions = custom_permissions
            
            db.session.commit()
            
            self.logger.info(
                f"User {user.email} approved by platform user {approved_by}"
            )
            
            # TODO: Send approval notification email
            
            return {
                'success': True,
                'message': f'User {user.email} approved successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'status': user.status.value,
                    'depot_access': user.depot_access,
                    'permissions': user.permissions
                }
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error approving user {user_id}: {str(e)}")
            raise
    
    def reject_user(self, user_id: int, rejected_by: int, reason: str) -> Dict:
        """
        Reject a pending customer user.
        
        Args:
            user_id: ID of user to reject
            rejected_by: ID of platform user rejecting
            reason: Reason for rejection
            
        Returns:
            Result dictionary with success status
        """
        try:
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
            
            # Update user status to rejected
            user.status = CustomerUserStatus.REJECTED
            user.updated_at = datetime.utcnow()
            
            # TODO: Store rejection reason in audit log
            
            db.session.commit()
            
            self.logger.info(
                f"User {user.email} rejected by platform user {rejected_by}. "
                f"Reason: {reason}"
            )
            
            # TODO: Send rejection notification email
            
            return {
                'success': True,
                'message': f'User {user.email} rejected',
                'reason': reason
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error rejecting user {user_id}: {str(e)}")
            raise
    
    # Customer Management Methods
    
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


from werkzeug.security import generate_password_hash
from application.models import db, Customer, CustomerUser

class AdminService:

    def create_customer_user(self, name, email, phone, password, customer_code, role, permission_code, permissions, depot_access):
        customer = Customer.query.filter_by(customer_code=customer_code).first()
        if not customer:
            return {
                "success": False,
                "error": "Customer not found",
                "code": "CUSTOMER_NOT_FOUND"
            }

        existing_user = CustomerUser.query.filter_by(email=email).first()
        if existing_user:
            return {
                "success": False,
                "error": "Email already in use",
                "code": "DUPLICATE_EMAIL"
            }

        new_user = CustomerUser(
            name=name,
            email=email,
            phone=phone,
            password=generate_password_hash(password),
            customer_id=customer.id,
            role=role,
            permission_code=permission_code,
            permissions=permissions,
            depot_access=depot_access,
            status='pending'
        )

        db.session.add(new_user)
        db.session.commit()

        return {
            "success": True,
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "status": new_user.status
            }
        }


# Create singleton instance
admin_service = AdminService()
