"""
Authentication Service Module

This module provides authentication functionality for the marketplace application,
supporting both CustomerUsers and PlatformUsers, including registration.

Key Features:
- Multi-user type authentication (CustomerUser and PlatformUser)
- Customer user registration with validation
- Password and phone number based authentication
- OTP generation and verification
- User status and role validation
- SMS integration for OTP delivery
- Session token generation with user type tracking
- Enhanced session payload with permissions

Classes:
    AuthService: Main authentication service class

Author: Development Team
Version: 5.0
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
import bcrypt
import requests
from requests.exceptions import RequestException

from application import db
from application.models.customer import Customer, CustomerStatus

# External API Configuration
EXTERNAL_API_BASE = 'http://102.33.60.228:9183/getResources/customers/'
EXTERNAL_API_USERNAME = 'd5900938-be95-4412-95b3-50b11983e13e'
EXTERNAL_API_PASSWORD = '90fa0de5-250a-4e99-bd65-85b1854d9c82'
from application.models.customer_user import CustomerUser, CustomerUserStatus, CustomerUserRole
from application.models.user_otp import UserOTP
from application.models.user_session import UserSession
from application.models.permission_code import PermissionCode
from application.services.helpers import auth_helpers

class AuthService:
    """
    Authentication service for password and phone-based OTP authentication.
    
    Handles both CustomerUser and PlatformUser authentication flows.
    """
    
    def __init__(self):
        """Initialize authentication service"""
        self.otp_expiry_minutes = 5
        self.otp_length = 6
        self.logger = logging.getLogger(__name__)
    
    def create_customer_user(self, registration_data: Dict) -> Dict:
        """
        Register a new customer user with soft validation against customer data.
        
        Args:
            registration_data: Dict containing:
                - full_name: User's full name (required)
                - email: User's email address (required)
                - password: User's password (required)
                - phone: User's phone number (required)
                - customer_code: Company's customer code (required)
                - customer_name: Company name for validation (required)
                - customer_account_number: Company account number for validation (required)
        
        Returns:
            Dict with success status and user data or error message
        """
        try:
            # Extract and validate required fields
            full_name = registration_data.get('full_name', '').strip()
            email = registration_data.get('email', '').strip().lower()
            password = registration_data.get('password', '')
            phone = registration_data.get('phone', '').strip()
            customer_code = registration_data.get('customer_code', '').strip()
            customer_name = registration_data.get('customer_name', '').strip()
            customer_account_number = registration_data.get('customer_account_number', '').strip()
            
            # Validate required fields
            if not all([full_name, email, password, phone, customer_code, customer_name, customer_account_number]):
                return {
                    'success': False,
                    'message': 'All fields are required: full name, email, password, phone, customer code, customer name, and account number',
                    'error_code': 'MISSING_FIELDS'
                }
            
            # Validate email format
            if not auth_helpers.validate_email(email):
                return {
                    'success': False,
                    'message': 'Invalid email format',
                    'error_code': 'INVALID_EMAIL'
                }
            
            # Validate phone format
            if not auth_helpers.validate_phone(phone):
                return {
                    'success': False,
                    'message': 'Invalid phone number format',
                    'error_code': 'INVALID_PHONE'
                }
            
            # Validate password strength
            if len(password) < 8:
                return {
                    'success': False,
                    'message': 'Password must be at least 8 characters long',
                    'error_code': 'WEAK_PASSWORD'
                }
            
            # Check if email already exists
            if CustomerUser.query.filter_by(email=email).first():
                return {
                    'success': False,
                    'message': 'Email address is already registered',
                    'error_code': 'EMAIL_EXISTS'
                }
            
            # Check if phone already exists
            if CustomerUser.query.filter_by(phone=phone).first():
                return {
                    'success': False,
                    'message': 'Phone number is already registered',
                    'error_code': 'PHONE_EXISTS'
                }
            
            # Initialize approval eligibility tracking
            approval_eligibility = {
                'status': 'ELIGIBLE',  # Will be updated based on validation
                'validation_date': datetime.utcnow().isoformat(),
                'mismatches': [],
                'warnings': []
            }
            
            # Soft validation of customer information
            customer = Customer.query.filter_by(
                customer_code=customer_code
            ).first()
            
            if not customer:
                # Customer code not found - this is a critical issue
                approval_eligibility['status'] = 'INELIGIBLE'
                approval_eligibility['mismatches'].append({
                    'field': 'customer_code',
                    'provided': customer_code,
                    'expected': None,
                    'message': 'Customer code not found in system'
                })
            else:
                # Validate customer details (soft validation)
                if customer.name.lower() != customer_name.lower():
                    approval_eligibility['status'] = 'REQUIRES_REVIEW'
                    approval_eligibility['mismatches'].append({
                        'field': 'customer_name',
                        'provided': customer_name,
                        'expected': customer.name,
                        'message': 'Customer name does not match records'
                    })
                
                if customer.account_number != customer_account_number:
                    approval_eligibility['status'] = 'REQUIRES_REVIEW'
                    approval_eligibility['mismatches'].append({
                        'field': 'customer_account_number',
                        'provided': customer_account_number,
                        'expected': customer.account_number,
                        'message': 'Account number does not match records'
                    })
                
                if customer.status != CustomerStatus.APPROVED:
                    approval_eligibility['warnings'].append({
                        'field': 'customer_status',
                        'current_status': customer.status.value,
                        'message': 'Customer account is not active'
                    })
                    # Don't set to INELIGIBLE as this might be temporary
                    if approval_eligibility['status'] == 'ELIGIBLE':
                        approval_eligibility['status'] = 'REQUIRES_REVIEW'
            
            # If customer not found, create a placeholder customer_id
            customer_id = customer.id if customer else None
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Get RESTRICTED permission code
            restricted_permission = PermissionCode.query.filter_by(
                code='RESTRICTED'
            ).first()
            
            # Create new user with OWNER role and RESTRICTED permissions
            new_user = CustomerUser(
                customer_id=customer_id,
                name=full_name,
                email=email,
                phone=phone,
                password=password_hash,
                role=CustomerUserRole.OWNER,  # Default to OWNER role
                permission_code='RESTRICTED' if restricted_permission else None,
                status=CustomerUserStatus.PENDING,  # Always pending as per Phase 2
                depot_access=[],  # Empty by default, assigned by admins later
                permissions={},    # Empty initially, will be populated on approval
                approval_eligibility=approval_eligibility  # Store validation results
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            self.logger.info(
                f"New customer user registered: {email} "
                f"with approval eligibility status: {approval_eligibility['status']}"
            )
            
            # Always return success to the user (soft validation)
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
                    'customer_name': customer_name  # Return what they provided
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
    
    def authenticate_with_password(self, email: str, password: str) -> Dict:
        """
        Authenticate customer user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict with authentication result and session token
        """
        try:
            # Find user by email
            user = CustomerUser.query.filter_by(email=email.lower()).first()
            
            if not user:
                return {
                    'success': False,
                    'message': 'Invalid email or password',
                    'error_code': 'INVALID_CREDENTIALS'
                }
            
            # Check password
            if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                return {
                    'success': False,
                    'message': 'Invalid email or password',
                    'error_code': 'INVALID_CREDENTIALS'
                }
            
            # Validate user status
            validation = auth_helpers.validate_customer_user_status(user)
            if not validation['valid']:
                return validation
            
            # Generate session token
            session_token = auth_helpers.generate_session_token()
            
            # Update last login
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            # Clear existing sessions for this user
            UserSession.query.filter_by(
                user_id=user.id, 
                user_type='customer_user'
            ).delete()
            
            # Create new session
            expires_at = datetime.utcnow() + timedelta(hours=24)
            user_session = UserSession(
                user_id=user.id,
                user_type='customer_user',
                session_token=session_token,
                expires_at=expires_at
            )
            db.session.add(user_session)
            db.session.commit()
            
            self.logger.info(f"User {email} authenticated successfully with password")
            
            return {
                'success': True,
                'message': 'Authentication successful',
                'session_token': session_token,
                'user_type': 'customer_user',
                'user': auth_helpers.build_customer_user_payload(user)
            }
            
        except Exception as e:
            self.logger.error(f"Error authenticating user {email}: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': 'Authentication failed. Please try again.',
                'error_code': 'AUTH_ERROR'
            }
    
    def send_otp(self, phone: str) -> Dict:
        """Send OTP to user's phone number (supports both user types)."""
        try:
            # Validate phone number format
            if not auth_helpers.validate_phone(phone):
                return {
                    'success': False,
                    'message': 'Invalid phone number format',
                    'error_code': 'INVALID_PHONE'
                }
            
            # Find user in either table
            user, user_type = auth_helpers.find_user_by_phone(phone)
            
            if not user:
                return {
                    'success': False,
                    'message': 'User not found. Please contact administrator.',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # Validate user status based on type
            if user_type == 'customer_user':
                validation = auth_helpers.validate_customer_user_status(user)
                if not validation['valid']:
                    return validation
            # Platform users don't need status validation
            
            # Generate and store OTP
            otp = auth_helpers.generate_otp(self.otp_length)
            hashed_otp = auth_helpers.hash_otp(otp)
            expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
            
            # Clear any existing OTPs for this phone
            UserOTP.query.filter_by(phone=phone).delete()
            
            # Store new OTP
            user_otp = UserOTP(
                phone=phone,
                otp_hash=hashed_otp,
                expires_at=expires_at,
                attempts=0
            )
            db.session.add(user_otp)
            db.session.commit()
            
            # Send SMS
            sms_sent = auth_helpers.send_sms(phone, otp, self.otp_length)
            
            if sms_sent:
                self.logger.info(f"OTP sent successfully to {phone} ({user_type})")
                return {
                    'success': True,
                    'message': f'OTP sent to {phone}',
                    'expires_in': self.otp_expiry_minutes * 60
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send SMS. Please try again.',
                    'error_code': 'SMS_FAILED'
                }
                
        except Exception as e:
            self.logger.error(f"Error sending OTP to {phone}: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': 'An error occurred. Please try again.',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def verify_otp(self, phone: str, otp: str) -> Dict:
        """Verify OTP and authenticate user (supports both user types)."""
        try:
            # Get stored OTP
            user_otp = UserOTP.query.filter(
                UserOTP.phone == phone,
                UserOTP.expires_at > datetime.utcnow()
            ).order_by(UserOTP.created_at.desc()).first()
            
            if not user_otp:
                return {
                    'success': False,
                    'message': 'OTP expired or not found. Please request a new one.',
                    'error_code': 'OTP_EXPIRED'
                }
            
            # Check attempt limit
            if user_otp.attempts >= 3:
                return {
                    'success': False,
                    'message': 'Too many failed attempts. Please request a new OTP.',
                    'error_code': 'TOO_MANY_ATTEMPTS'
                }
            
            # Verify OTP
            if auth_helpers.hash_otp(otp) != user_otp.otp_hash:
                # Increment attempts
                user_otp.attempts += 1
                db.session.commit()
                return {
                    'success': False,
                    'message': 'Invalid OTP. Please try again.',
                    'error_code': 'INVALID_OTP'
                }
            
            # OTP is valid, get user data
            user, user_type = auth_helpers.find_user_by_phone(phone)
            
            if not user:
                return {
                    'success': False,
                    'message': 'User not found',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # Final validation for customer users
            if user_type == 'customer_user':
                validation = auth_helpers.validate_customer_user_status(user)
                if not validation['valid']:
                    return validation
            
            # Generate session token
            session_token = auth_helpers.generate_session_token()
            
            # Update last login
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            # Clear used OTP
            UserOTP.query.filter_by(phone=phone).delete()
            
            # Clear existing sessions for this user
            UserSession.query.filter_by(
                user_id=user.id, 
                user_type=user_type
            ).delete()
            
            # Create new session
            expires_at = datetime.utcnow() + timedelta(hours=24)
            user_session = UserSession(
                user_id=user.id,
                user_type=user_type,
                session_token=session_token,
                expires_at=expires_at
            )
            db.session.add(user_session)
            db.session.commit()
            
            self.logger.info(f"User {phone} ({user_type}) authenticated successfully")
            
            # Build response based on user type
            response = {
                'success': True,
                'message': 'Authentication successful',
                'session_token': session_token,
                'user_type': user_type
            }
            
            if user_type == 'customer_user':
                response['user'] = auth_helpers.build_customer_user_payload(user)
            else:
                response['user'] = auth_helpers.build_platform_user_payload(user)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error verifying OTP for {phone}: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': 'An error occurred. Please try again.',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def validate_session(self, session_token: str) -> Dict:
        """Validate session token and get user data."""
        try:
            session = UserSession.query.filter(
                UserSession.session_token == session_token,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                return {'valid': False, 'error': 'Invalid or expired session'}
            
            # Get the user based on user_type
            user = session.user  # This uses the polymorphic property
            
            if not user:
                return {'valid': False, 'error': 'User not found'}
            
            # Build response based on user type
            response = {
                'valid': True,
                'user_type': session.user_type
            }
            
            if session.user_type == 'customer_user':
                # Additional validation for customer users
                if user.status != CustomerUserStatus.APPROVED:
                    return {'valid': False, 'error': 'User not approved'}
                if user.customer.status.value != 'approved':
                    return {'valid': False, 'error': 'Customer not active'}
                response['user'] = auth_helpers.build_customer_user_payload(user)
            else:
                response['user'] = auth_helpers.build_platform_user_payload(user)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error validating session: {e}")
            return {'valid': False, 'error': 'Session validation failed'}
    
    def logout(self, session_token: str) -> bool:
        """Logout user by invalidating session token."""
        try:
            result = UserSession.query.filter_by(session_token=session_token).delete()
            db.session.commit()
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Error during logout: {e}")
            db.session.rollback()
            return False