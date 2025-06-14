"""
Authentication Service Module

This module provides authentication functionality for the marketplace application,
using SQLAlchemy models for database operations.

Key Features:
- Phone number based authentication
- OTP generation and verification
- User status and role validation
- SMS integration for OTP delivery
- Session token generation
- Uses SQLAlchemy models (no custom database handling)

Classes:
    AuthService: Main authentication service class

Dependencies:
    - SQLAlchemy models for database operations
    - SMS service for OTP delivery
    - Random number generation for OTP
    - Datetime for expiration handling

Usage:
    auth_service = AuthService()
    result = auth_service.send_otp(phone_number)

Author: Development Team
Version: 2.0
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict
import logging
import hashlib
import secrets

from application import db
from application.models.user import User
from application.models.user_otp import UserOTP
from application.models.user_session import UserSession

class AuthService:
    """
    Authentication service for phone-based OTP authentication.
    
    Handles user authentication flow using SQLAlchemy models.
    """
    
    def __init__(self):
        """Initialize authentication service"""
        self.otp_expiry_minutes = 5  # OTP expires in 5 minutes
        self.otp_length = 6
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def generate_otp(self) -> str:
        """Generate a random OTP code."""
        return ''.join(random.choices(string.digits, k=self.otp_length))
    
    def hash_otp(self, otp: str) -> str:
        """Hash OTP for secure storage."""
        return hashlib.sha256(otp.encode()).hexdigest()
    
    def send_otp(self, phone: str) -> Dict:
        """Send OTP to user's phone number."""
        try:
            # Validate phone number format
            if not self._validate_phone(phone):
                return {
                    'success': False,
                    'message': 'Invalid phone number format',
                    'error_code': 'INVALID_PHONE'
                }
            
            # Check if user exists and is approved
            user = User.find_by_phone(phone)
            if not user:
                return {
                    'success': False,
                    'message': 'User not found. Please contact administrator.',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            if not user.is_approved():
                return {
                    'success': False,
                    'message': 'Account not approved. Please contact administrator.',
                    'error_code': 'USER_NOT_APPROVED'
                }
            
            # Generate OTP
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
                logging.info(f"OTP sent successfully to {phone}")
                return {
                    'success': True,
                    'message': f'OTP sent to {phone}',
                    'expires_in': self.otp_expiry_minutes * 60  # seconds
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send SMS. Please try again.',
                    'error_code': 'SMS_FAILED'
                }
                
        except Exception as e:
            logging.error(f"Error sending OTP to {phone}: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': 'An error occurred. Please try again.',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def verify_otp(self, phone: str, otp: str) -> Dict:
        """Verify OTP and authenticate user."""
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
            user = User.get_approved_user_by_phone(phone)
            if not user:
                return {
                    'success': False,
                    'message': 'User not found or not approved',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # Generate session token
            session_token = self._generate_session_token()
            
            # Update last login
            user.update_last_login()
            
            # Clear used OTP
            UserOTP.query.filter_by(phone=phone).delete()
            
            # Clear existing sessions and store new session
            UserSession.query.filter_by(user_id=user.id).delete()
            
            expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hour session
            user_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                expires_at=expires_at
            )
            db.session.add(user_session)
            db.session.commit()
            
            logging.info(f"User {phone} authenticated successfully")
            
            return {
                'success': True,
                'message': 'Authentication successful',
                'user': user.to_dict(),
                'session_token': session_token
            }
            
        except Exception as e:
            logging.error(f"Error verifying OTP for {phone}: {e}")
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
            
            if session and session.user.is_approved():
                return {
                    'valid': True,
                    'user': session.user.to_dict()
                }
            else:
                return {'valid': False, 'error': 'Invalid or expired session'}
                
        except Exception as e:
            logging.error(f"Error validating session: {e}")
            return {'valid': False, 'error': 'Session validation failed'}
    
    def logout(self, session_token: str) -> bool:
        """Logout user by invalidating session token."""
        try:
            result = UserSession.query.filter_by(session_token=session_token).delete()
            db.session.commit()
            return result > 0
            
        except Exception as e:
            logging.error(f"Error during logout: {e}")
            db.session.rollback()
            return False
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        import re
        pattern = r'^(\+27|0)[0-9]{9}$'
        return bool(re.match(pattern, phone))
    
    def _send_sms(self, phone: str, otp: str) -> bool:
        """Send SMS with OTP (mock implementation)"""
        try:
            message = f"Your OTP code is: {otp}. Valid for {self.otp_expiry_minutes} minutes."
            logging.info(f"SMS to {phone}: {message}")
            return True  # Mock success
            
        except Exception as e:
            logging.error(f"Error sending SMS to {phone}: {e}")
            return False
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)