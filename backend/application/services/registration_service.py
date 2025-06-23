"""
Registration Service Module

Handles new customer user registration with multi-tenant support.

Key Features:
- Single-step registration with customer code validation
- All users start with pending status
- Role-based registration
- No self-assigned depot access

Author: Development Team
Version: 2.0
"""

import logging
from typing import Dict
from application import db
from application.models.customer import Customer, CustomerStatus
from application.models.customer_user import CustomerUser, CustomerUserStatus, CustomerUserRole
from application.models.permission_code import PermissionCode

class RegistrationService:
    """Handle customer user registration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def register_customer_user(self, registration_data: Dict) -> Dict:
        """
        Register a new customer user with single-step process.
        
        Args:
            registration_data: Dict containing:
                - customer_code: Company's customer code
                - name: User's full name
                - email: User's email address
                - phone: User's phone number (optional)
                - role: Requested role (owner, staff, viewer)
        
        Returns:
            Dict with success status and user data or error message
        """
        try:
            # Extract and validate required fields
            customer_code = registration_data.get('customer_code', '').strip()
            name = registration_data.get('name', '').strip()
            email = registration_data.get('email', '').strip().lower()
            phone = registration_data.get('phone', '').strip() if registration_data.get('phone') else None
            role_str = registration_data.get('role', 'viewer').lower()
            
            # Validate required fields
            if not all([customer_code, name, email]):
                return {
                    'success': False,
                    'message': 'Customer code, name, and email are required',
                    'error_code': 'MISSING_FIELDS'
                }
            
            # Validate role
            try:
                if role_str not in ['owner', 'staff', 'viewer']:
                    return {
                        'success': False,
                        'message': 'Invalid role. Must be owner, staff, or viewer',
                        'error_code': 'INVALID_ROLE'
                    }
                requested_role = CustomerUserRole[role_str.upper()]
            except KeyError:
                return {
                    'success': False,
                    'message': 'Invalid role specified',
                    'error_code': 'INVALID_ROLE'
                }
            
            # Validate customer code
            customer = Customer.query.filter_by(
                customer_code=customer_code
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'message': 'Invalid customer code. Please contact your administrator.',
                    'error_code': 'INVALID_CUSTOMER_CODE'
                }
            
            if customer.status != CustomerStatus.APPROVED:
                return {
                    'success': False,
                    'message': 'Customer account is not active. Please contact support.',
                    'error_code': 'CUSTOMER_NOT_ACTIVE'
                }
            
            # Check if email already exists
            if CustomerUser.query.filter_by(email=email).first():
                return {
                    'success': False,
                    'message': 'Email address is already registered',
                    'error_code': 'EMAIL_EXISTS'
                }
            
            # Check if phone already exists
            if phone and CustomerUser.query.filter_by(phone=phone).first():
                return {
                    'success': False,
                    'message': 'Phone number is already registered',
                    'error_code': 'PHONE_EXISTS'
                }
            
            # Get appropriate permission code for the role
            permission_code = PermissionCode.query.filter_by(
                role=requested_role.value
            ).first()
            
            # Create new user with pending status (as per Phase 2 requirements)
            new_user = CustomerUser(
                customer_id=customer.id,
                name=name,
                email=email,
                phone=phone,
                role=requested_role,
                permission_code=permission_code.code if permission_code else None,
                status=CustomerUserStatus.PENDING,  # Always pending as per Phase 2
                depot_access=[],  # Empty by default, assigned by admins later
                permissions={}    # Custom permissions assigned later if needed
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            self.logger.info(
                f"New user registered: {email} for customer {customer.name} "
                f"with role {requested_role.value} - pending approval"
            )
            
            return {
                'success': True,
                'message': 'Registration successful. Your account is pending approval from your company administrator.',
                'user': {
                    'id': new_user.id,
                    'name': new_user.name,
                    'email': new_user.email,
                    'phone': new_user.phone,
                    'role': new_user.role.value,
                    'status': new_user.status.value,
                    'customer_name': customer.name
                }
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error registering user: {str(e)}")
            return {
                'success': False,
                'message': 'Registration failed. Please try again.',
                'error_code': 'REGISTRATION_ERROR'
            }
    
    def check_registration_eligibility(self, email: str) -> Dict:
        """
        Check if an email is eligible for registration.
        
        Args:
            email: Email address to check
            
        Returns:
            Dict with eligibility status
        """
        try:
            # Check CustomerUser table
            if CustomerUser.query.filter_by(email=email.lower()).first():
                return {
                    'eligible': False,
                    'reason': 'Email already registered as customer user'
                }
            
            # Check PlatformUser table
            from application.models.platform_user import PlatformUser
            if PlatformUser.query.filter_by(email=email.lower()).first():
                return {
                    'eligible': False,
                    'reason': 'Email already registered as platform user'
                }
            
            return {
                'eligible': True,
                'message': 'Email is available for registration'
            }
            
        except Exception as e:
            self.logger.error(f"Error checking registration eligibility: {str(e)}")
            return {
                'eligible': False,
                'reason': 'Unable to verify email eligibility'
            }

# Create singleton instance
registration_service = RegistrationService()