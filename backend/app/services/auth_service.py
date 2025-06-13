"""
Authentication Service Module

This module provides authentication functionality for the marketplace application,
including phone-based OTP authentication, user verification, and session management.

Key Features:
- Phone number based authentication
- OTP generation and verification
- User status and role validation
- SMS integration for OTP delivery
- Session token generation

Classes:
    AuthService: Main authentication service class

Dependencies:
    - User model for database operations
    - SMS service for OTP delivery
    - Random number generation for OTP
    - Datetime for expiration handling

Usage:
    auth_service = AuthService()
    result = auth_service.send_otp(phone_number)

Author: Development Team
Version: 1.0
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
from ..models.user import User, UserStatus
from ..utils.database import DatabaseConnection
import hashlib
import secrets

class AuthService:
    """
    Authentication service for phone-based OTP authentication.
    
    Handles user authentication flow including OTP generation,
    SMS delivery, verification, and session management.
    """
    
    def __init__(self):
        """Initialize authentication service"""
        self.db = DatabaseConnection()
        self.otp_expiry_minutes = 5  # OTP expires in 5 minutes
        self.otp_length = 6
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def generate_otp(self) -> str:
        """
        Generate a random OTP code.
        
        Returns:
            str: 6-digit OTP code
        """
        return ''.join(random.choices(string.digits, k=self.otp_length))
    
    def hash_otp(self, otp: str) -> str:
        """
        Hash OTP for secure storage.
        
        Args:
            otp (str): Plain text OTP
            
        Returns:
            str: Hashed OTP
        """
        return hashlib.sha256(otp.encode()).hexdigest()
    
    def send_otp(self, phone: str) -> Dict:
        """
        Send OTP to user's phone number.
        
        Args:
            phone (str): User's phone number
            
        Returns:
            dict: Result with success status and message
        """
        try:
            # Validate phone number format
            if not self._validate_phone(phone):
                return {
                    'success': False,
                    'message': 'Invalid phone number format',
                    'error_code': 'INVALID_PHONE'
                }
            
            # Check if user exists and is approved
            if not self.db.connect():
                return {
                    'success': False,
                    'message': 'Database connection failed',
                    'error_code': 'DB_ERROR'
                }
            
            try:
                # Check user exists and status
                user_query = """
                    SELECT id, phone, name, status, role 
                    FROM users 
                    WHERE phone = %s
                """
                user_result = self.db.execute_query(user_query, (phone,))
                
                if not user_result:
                    return {
                        'success': False,
                        'message': 'User not found. Please contact administrator.',
                        'error_code': 'USER_NOT_FOUND'
                    }
                
                user_data = user_result[0]
                user_status = user_data[3]
                
                if user_status != 'approved':
                    return {
                        'success': False,
                        'message': 'Account not approved. Please contact administrator.',
                        'error_code': 'USER_NOT_APPROVED'
                    }
                
                # Generate OTP
                otp = self.generate_otp()
                hashed_otp = self.hash_otp(otp)
                expires_at = datetime.now() + timedelta(minutes=self.otp_expiry_minutes)
                
                # Store OTP in database
                self._store_otp(phone, hashed_otp, expires_at)
                
                # Send SMS (implement actual SMS service)
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
                    
            finally:
                self.db.disconnect()
                
        except Exception as e:
            logging.error(f"Error sending OTP to {phone}: {e}")
            return {
                'success': False,
                'message': 'An error occurred. Please try again.',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def verify_otp(self, phone: str, otp: str) -> Dict:
        """
        Verify OTP and authenticate user.
        
        Args:
            phone (str): User's phone number
            otp (str): OTP code to verify
            
        Returns:
            dict: Authentication result with user data and session token
        """
        try:
            if not self.db.connect():
                return {
                    'success': False,
                    'message': 'Database connection failed',
                    'error_code': 'DB_ERROR'
                }
            
            try:
                # Get stored OTP
                otp_query = """
                    SELECT otp_hash, expires_at, attempts 
                    FROM user_otps 
                    WHERE phone = %s 
                    AND expires_at > NOW()
                    ORDER BY created_at DESC 
                    LIMIT 1
                """
                otp_result = self.db.execute_query(otp_query, (phone,))
                
                if not otp_result:
                    return {
                        'success': False,
                        'message': 'OTP expired or not found. Please request a new one.',
                        'error_code': 'OTP_EXPIRED'
                    }
                
                stored_hash = otp_result[0][0]
                expires_at = otp_result[0][1]
                attempts = otp_result[0][2]
                
                # Check attempt limit
                if attempts >= 3:
                    return {
                        'success': False,
                        'message': 'Too many failed attempts. Please request a new OTP.',
                        'error_code': 'TOO_MANY_ATTEMPTS'
                    }
                
                # Verify OTP
                if self.hash_otp(otp) != stored_hash:
                    # Increment attempts
                    self._increment_otp_attempts(phone)
                    return {
                        'success': False,
                        'message': 'Invalid OTP. Please try again.',
                        'error_code': 'INVALID_OTP'
                    }
                
                # OTP is valid, get user data
                user_query = """
                    SELECT id, phone, name, email, role, status, customer_code
                    FROM users 
                    WHERE phone = %s AND status = 'approved'
                """
                user_result = self.db.execute_query(user_query, (phone,))
                
                if not user_result:
                    return {
                        'success': False,
                        'message': 'User not found or not approved',
                        'error_code': 'USER_NOT_FOUND'
                    }
                
                user_data = user_result[0]
                
                # Generate session token
                session_token = self._generate_session_token()
                
                # Update last login
                self._update_last_login(phone)
                
                # Clear used OTP
                self._clear_otp(phone)
                
                # Store session
                self._store_session(user_data[0], session_token)
                
                logging.info(f"User {phone} authenticated successfully")
                
                return {
                    'success': True,
                    'message': 'Authentication successful',
                    'user': {
                        'id': user_data[0],
                        'phone': user_data[1],
                        'name': user_data[2],
                        'email': user_data[3],
                        'role': user_data[4],
                        'status': user_data[5],
                        'customer_code': user_data[6]
                    },
                    'session_token': session_token
                }
                
            finally:
                self.db.disconnect()
                
        except Exception as e:
            logging.error(f"Error verifying OTP for {phone}: {e}")
            return {
                'success': False,
                'message': 'An error occurred. Please try again.',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def validate_session(self, session_token: str) -> Dict:
        """
        Validate session token and get user data.
        
        Args:
            session_token (str): Session token to validate
            
        Returns:
            dict: Validation result with user data
        """
        try:
            if not self.db.connect():
                return {'valid': False, 'error': 'Database connection failed'}
            
            try:
                session_query = """
                    SELECT u.id, u.phone, u.name, u.email, u.role, u.status, u.customer_code
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = %s 
                    AND s.expires_at > NOW()
                    AND u.status = 'approved'
                """
                result = self.db.execute_query(session_query, (session_token,))
                
                if result:
                    user_data = result[0]
                    return {
                        'valid': True,
                        'user': {
                            'id': user_data[0],
                            'phone': user_data[1],
                            'name': user_data[2],
                            'email': user_data[3],
                            'role': user_data[4],
                            'status': user_data[5],
                            'customer_code': user_data[6]
                        }
                    }
                else:
                    return {'valid': False, 'error': 'Invalid or expired session'}
                    
            finally:
                self.db.disconnect()
                
        except Exception as e:
            logging.error(f"Error validating session: {e}")
            return {'valid': False, 'error': 'Session validation failed'}
    
    def logout(self, session_token: str) -> bool:
        """
        Logout user by invalidating session token.
        
        Args:
            session_token (str): Session token to invalidate
            
        Returns:
            bool: True if session was found and invalidated
        """
        try:
            if not self.db.connect():
                return False
            
            try:
                # Delete session
                delete_query = "DELETE FROM user_sessions WHERE session_token = %s"
                result = self.db.execute_query(delete_query, (session_token,))
                
                return result > 0  # Returns True if a row was deleted
                
            finally:
                self.db.disconnect()
                
        except Exception as e:
            logging.error(f"Error during logout: {e}")
            return False
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        # Basic South African phone number validation
        import re
        pattern = r'^(\+27|0)[0-9]{9}$'
        return bool(re.match(pattern, phone))
    
    def _store_otp(self, phone: str, hashed_otp: str, expires_at: datetime):
        """Store OTP in database"""
        try:
            # First, create the table if it doesn't exist
            self._create_otp_table()
            
            # Clear any existing OTPs for this phone
            clear_query = "DELETE FROM user_otps WHERE phone = %s"
            self.db.execute_query(clear_query, (phone,))
            
            # Insert new OTP
            insert_query = """
                INSERT INTO user_otps (phone, otp_hash, expires_at, attempts, created_at)
                VALUES (%s, %s, %s, 0, NOW())
            """
            self.db.execute_query(insert_query, (phone, hashed_otp, expires_at))
            
        except Exception as e:
            logging.error(f"Error storing OTP: {e}")
            raise
    
    def _send_sms(self, phone: str, otp: str) -> bool:
        """
        Send SMS with OTP (implement with actual SMS service)
        
        For now, this is a mock implementation.
        Replace with actual SMS service integration.
        """
        try:
            # Mock SMS sending - replace with actual SMS service
            message = f"Your OTP code is: {otp}. Valid for {self.otp_expiry_minutes} minutes."
            
            # For development, log the OTP
            logging.info(f"SMS to {phone}: {message}")
            
            # TODO: Integrate with actual SMS service (Twilio, etc.)
            # Example:
            # sms_client.send_message(phone, message)
            
            return True  # Mock success
            
        except Exception as e:
            logging.error(f"Error sending SMS to {phone}: {e}")
            return False
    
    def _increment_otp_attempts(self, phone: str):
        """Increment OTP attempt counter"""
        try:
            update_query = """
                UPDATE user_otps 
                SET attempts = attempts + 1 
                WHERE phone = %s 
                AND expires_at > NOW()
            """
            self.db.execute_query(update_query, (phone,))
        except Exception as e:
            logging.error(f"Error incrementing OTP attempts: {e}")
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def _update_last_login(self, phone: str):
        """Update user's last login timestamp"""
        try:
            update_query = """
                UPDATE users 
                SET last_login = NOW(), updated_at = NOW() 
                WHERE phone = %s
            """
            self.db.execute_query(update_query, (phone,))
        except Exception as e:
            logging.error(f"Error updating last login: {e}")
    
    def _clear_otp(self, phone: str):
        """Clear used OTP"""
        try:
            delete_query = "DELETE FROM user_otps WHERE phone = %s"
            self.db.execute_query(delete_query, (phone,))
        except Exception as e:
            logging.error(f"Error clearing OTP: {e}")
    
    def _store_session(self, user_id: int, session_token: str):
        """Store session token"""
        try:
            # Create sessions table if needed
            self._create_sessions_table()
            
            # Clear existing sessions for user
            clear_query = "DELETE FROM user_sessions WHERE user_id = %s"
            self.db.execute_query(clear_query, (user_id,))
            
            # Store new session
            expires_at = datetime.now() + timedelta(hours=24)  # 24 hour session
            insert_query = """
                INSERT INTO user_sessions (user_id, session_token, expires_at, created_at)
                VALUES (%s, %s, %s, NOW())
            """
            self.db.execute_query(insert_query, (user_id, session_token, expires_at))
            
        except Exception as e:
            logging.error(f"Error storing session: {e}")
            raise
    
    def _create_otp_table(self):
        """Create OTP table if it doesn't exist"""
        schema = """
            id INT AUTO_INCREMENT PRIMARY KEY,
            phone VARCHAR(15) NOT NULL,
            otp_hash VARCHAR(64) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            attempts INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_phone (phone),
            INDEX idx_expires (expires_at)
        """
        self.db.create_table_if_not_exists('user_otps', schema)
    
    def _create_sessions_table(self):
        """Create sessions table if it doesn't exist"""
        schema = """
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            session_token VARCHAR(64) NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_token (session_token),
            INDEX idx_user (user_id),
            INDEX idx_expires (expires_at),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        """
        self.db.create_table_if_not_exists('user_sessions', schema)