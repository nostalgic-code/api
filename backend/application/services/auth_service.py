"""
Authentication Service Module

This module provides authentication functionality for the marketplace application,
supporting both CustomerUsers and PlatformUsers.

Key Features:
- Multi-user type authentication (CustomerUser and PlatformUser)
- Phone number based authentication
- OTP generation and verification
- User status and role validation
- SMS integration for OTP delivery
- Session token generation with user type tracking
- Enhanced session payload with permissions

Classes:
    AuthService: Main authentication service class

Author: Development Team
Version: 4.0
"""

import re
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional, Union
import logging
import hashlib
import secrets

from application import db
from application.models.customer_user import CustomerUser, CustomerUserStatus
from application.models.platform_user import PlatformUser
from application.models.user_otp import UserOTP
from application.models.user_session import UserSession
from application.models.permission_code import PermissionCode
from application.services.sms_service import sms_service

class AuthService:
    """
    Authentication service for phone-based OTP authentication.
    
    Handles both CustomerUser and PlatformUser authentication flows.
    """
    
    def __init__(self):
        """Initialize authentication service"""
        self.otp_expiry_minutes = 5
        self.otp_length = 6
        self.logger = logging.getLogger(__name__)
    
    def generate_otp(self) -> str:
        """Generate a random OTP code."""
        return ''.join(random.choices(string.digits, k=self.otp_length))
    
    def hash_otp(self, otp: str) -> str:
        """Hash OTP for secure storage."""
        return hashlib.sha256(otp.encode()).hexdigest()
    
    def send_otp(self, phone: str) -> Dict:
        """Send OTP to user's phone number (supports both user types)."""
        try:
            # Validate phone number format
            if not self._validate_phone(phone):
                return {
                    'success': False,
                    'message': 'Invalid phone number format',
                    'error_code': 'INVALID_PHONE'
                }
            
            # Find user in either table
            user, user_type = self._find_user_by_phone(phone)
            
            if not user:
                return {
                    'success': False,
                    'message': 'User not found. Please contact administrator.',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # Validate user status based on type
            if user_type == 'customer_user':
                validation = self._validate_customer_user_status(user)
                if not validation['valid']:
                    return validation
            # Platform users don't need status validation
            
            # Generate and store OTP
            otp = self.generate_otp()
            hashed_otp = self.hash_otp(otp)
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
            sms_sent = self._send_sms(phone, otp)
            
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
            if self.hash_otp(otp) != user_otp.otp_hash:
                # Increment attempts
                user_otp.attempts += 1
                db.session.commit()
                return {
                    'success': False,
                    'message': 'Invalid OTP. Please try again.',
                    'error_code': 'INVALID_OTP'
                }
            
            # OTP is valid, get user data
            user, user_type = self._find_user_by_phone(phone)
            
            if not user:
                return {
                    'success': False,
                    'message': 'User not found',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # Final validation for customer users
            if user_type == 'customer_user':
                validation = self._validate_customer_user_status(user)
                if not validation['valid']:
                    return validation
            
            # Generate session token
            session_token = self._generate_session_token()
            
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
                response['user'] = self._build_customer_user_payload(user)
            else:
                response['user'] = self._build_platform_user_payload(user)
            
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
                response['user'] = self._build_customer_user_payload(user)
            else:
                response['user'] = self._build_platform_user_payload(user)
            
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
    
    # Helper methods
    def _find_user_by_phone(self, phone: str) -> tuple[Optional[Union[CustomerUser, PlatformUser]], Optional[str]]:
        """Find user in either CustomerUser or PlatformUser table"""
        # Check CustomerUser first
        customer_user = CustomerUser.query.filter_by(phone=phone).first()
        if customer_user:
            return customer_user, 'customer_user'
        
        # Check PlatformUser
        platform_user = PlatformUser.query.filter_by(phone=phone).first()
        if platform_user:
            return platform_user, 'platform_user'
        
        return None, None
    
    def _validate_customer_user_status(self, user: CustomerUser) -> Dict:
        """Validate customer user and their parent customer status"""
        if user.status != CustomerUserStatus.APPROVED:
            return {
                'valid': False,
                'success': False,
                'message': 'Your account is pending approval.',
                'error_code': 'USER_NOT_APPROVED'
            }
        
        if user.customer.status.value != 'approved':
            return {
                'valid': False,
                'success': False,
                'message': 'Customer account is not active.',
                'error_code': 'CUSTOMER_NOT_ACTIVE'
            }
        
        return {'valid': True}
    
    def _build_customer_user_payload(self, user: CustomerUser) -> Dict:
        """Build enhanced payload for customer users"""
        # Get effective permissions
        effective_permissions = self._calculate_effective_permissions(user)
        
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'customer_id': user.customer_id,
            'customer_name': user.customer.name if user.customer else None,
            'role': user.role.value if user.role else None,
            'permissions': effective_permissions,
            'depot_access': user.depot_access or [],
            'status': user.status.value if user.status else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
    
    def _build_platform_user_payload(self, user: PlatformUser) -> Dict:
        """Build payload for platform users"""
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role.value if user.role else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
    
    def _calculate_effective_permissions(self, user: CustomerUser) -> Dict:
        """Calculate effective permissions by merging default and custom"""
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
                    permissions[key].update(value)
                else:
                    permissions[key] = value
        
        return permissions
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        pattern = r'^(\+27|0)[0-9]{9}$'
        return bool(re.match(pattern, phone))
    
    def _send_sms(self, phone: str, otp: str) -> bool:
        """Send SMS with OTP using BulkSMS service"""
        try:
            # Log OTP to console for development
            self.logger.warning(f"=== OTP FOR DEVELOPMENT ===")
            self.logger.warning(f"Phone: {phone}")
            self.logger.warning(f"OTP Code: {otp}")
            self.logger.warning(f"===========================")
            
            # Try to send SMS but don't fail if it doesn't work
            try:
                success = sms_service.send_otp(phone, otp)
                if success:
                    self.logger.info(f"SMS sent successfully to {phone}")
                else:
                    self.logger.warning(f"SMS service failed for {phone}, but OTP is logged above")
            except Exception as sms_error:
                self.logger.warning(f"SMS service error for {phone}: {sms_error}, but OTP is logged above")
            
            # Always return True in development so the flow continues
            return True
            
        except Exception as e:
            self.logger.error(f"Error in _send_sms for {phone}: {e}")
            return False
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)