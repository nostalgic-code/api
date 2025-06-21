"""
Authentication API Module

This module provides RESTful API endpoints for user authentication
including phone-based OTP authentication, session management, and
new user registration for the multi-tenant system.

Key Features:
- Customer user registration with company code validation
- Multi-user type authentication (CustomerUser and PlatformUser)
- Phone number based authentication
- OTP generation and SMS delivery
- OTP verification and user authentication
- Session token management with user type tracking
- Role-based access control

Endpoints:
    POST /auth/register - Register new customer user
    POST /auth/send-otp - Send OTP to user's phone
    POST /auth/verify-otp - Verify OTP and authenticate user
    POST /auth/validate-session - Validate session token
    POST /auth/logout - Logout and invalidate session
    GET /auth/user-info - Get current user information

Author: Development Team
Version: 2.0
"""

from flask import Blueprint, request, jsonify
import logging
from ..services.auth_service import AuthService
from ..services.registration_service import registration_service

# Create Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Initialize auth service
auth_service = AuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new customer user (single-step process).
    
    Request Body:
        {
            "customer_code": "CUST001",
            "name": "John Doe",
            "email": "john@company.com",
            "phone": "+27123456789",  // optional
            "role": "staff"  // owner, staff, or viewer
        }
    
    Response:
        {
            "success": true,
            "message": "Registration successful. Your account is pending approval.",
            "user": {
                "id": 1,
                "name": "John Doe",
                "email": "john@company.com",
                "phone": "+27123456789",
                "role": "staff",
                "status": "pending",
                "customer_name": "ABC Company"
            },
            "requires_approval": true
        }
    
    Note: First user for a customer automatically becomes owner with approved status.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        # Validate email format
        email = data.get('email', '').strip().lower()
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({
                    'success': False,
                    'message': 'Invalid email format',
                    'error_code': 'INVALID_EMAIL'
                }), 400
        
        # Validate phone format if provided
        phone = data.get('phone', '').strip()
        if phone:
            import re
            phone_pattern = r'^(\+27|0)[0-9]{9}$'
            if not re.match(phone_pattern, phone):
                return jsonify({
                    'success': False,
                    'message': 'Invalid phone format. Use +27XXXXXXXXX or 0XXXXXXXXX',
                    'error_code': 'INVALID_PHONE'
                }), 400
        
        # Call registration service
        result = registration_service.register_customer_user(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            # Return appropriate status code based on error
            status_code = 400
            if result.get('error_code') in ['INVALID_CUSTOMER_CODE', 'CUSTOMER_NOT_ACTIVE']:
                status_code = 404
            elif result.get('error_code') in ['EMAIL_EXISTS', 'PHONE_EXISTS']:
                status_code = 409
            
            return jsonify(result), status_code
            
    except Exception as e:
        logging.error(f"Error in registration endpoint: {e}")
        return jsonify({
            'success': False,
            'message': 'An internal error occurred',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/check-email', methods=['POST'])
def check_email():
    """
    Check if an email is available for registration.
    
    Request Body:
        {
            "email": "john@company.com"
        }
    
    Response:
        {
            "eligible": true,
            "message": "Email is available for registration"
        }
    """
    try:
        data = request.get_json()
        if not data or not data.get('email'):
            return jsonify({
                'eligible': False,
                'reason': 'Email is required'
            }), 400
        
        email = data.get('email', '').strip().lower()
        result = registration_service.check_registration_eligibility(email)
        
        return jsonify(result), 200 if result['eligible'] else 409
        
    except Exception as e:
        logging.error(f"Error checking email: {e}")
        return jsonify({
            'eligible': False,
            'reason': 'Unable to check email availability'
        }), 500

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """
    Send OTP to user's phone number.
    
    Now supports both CustomerUser and PlatformUser authentication.
    
    Request Body:
        phone (str): User's phone number
    
    Returns:
        JSON: Success/error response with OTP status
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required',
                'error_code': 'MISSING_DATA'
            }), 400
        
        phone = data.get('phone', '').strip()
        if not phone:
            return jsonify({
                'success': False,
                'message': 'Phone number is required',
                'error_code': 'MISSING_PHONE'
            }), 400
        
        # Send OTP
        result = auth_service.send_otp(phone)
        
        if result['success']:
            return jsonify(result), 200
        else:
            # Return appropriate status code based on error
            status_code = 400
            if result.get('error_code') in ['USER_NOT_FOUND', 'USER_NOT_APPROVED', 'CUSTOMER_NOT_ACTIVE']:
                status_code = 403
            elif result.get('error_code') == 'DB_ERROR':
                status_code = 500
            
            return jsonify(result), status_code
    
    except Exception as e:
        logging.error(f"Error in send_otp endpoint: {e}")
        return jsonify({
            'success': False,
            'message': 'An internal error occurred',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP and authenticate user.
    
    Now returns enhanced payload with user_type and permissions.
    
    Request Body:
        phone (str): User's phone number
        otp (str): OTP code to verify
    
    Returns:
        JSON: Authentication result with user data, session token, and user type
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required',
                'error_code': 'MISSING_DATA'
            }), 400
        
        phone = data.get('phone', '').strip()
        otp = data.get('otp', '').strip()
        
        if not phone:
            return jsonify({
                'success': False,
                'message': 'Phone number is required',
                'error_code': 'MISSING_PHONE'
            }), 400
        
        if not otp:
            return jsonify({
                'success': False,
                'message': 'OTP is required',
                'error_code': 'MISSING_OTP'
            }), 400
        
        # Verify OTP
        result = auth_service.verify_otp(phone, otp)
        
        if result['success']:
            return jsonify(result), 200
        else:
            # Return appropriate status code based on error
            status_code = 400
            if result.get('error_code') in ['USER_NOT_FOUND', 'TOO_MANY_ATTEMPTS']:
                status_code = 403
            elif result.get('error_code') == 'DB_ERROR':
                status_code = 500
            
            return jsonify(result), status_code
    
    except Exception as e:
        logging.error(f"Error in verify_otp endpoint: {e}")
        return jsonify({
            'success': False,
            'message': 'An internal error occurred',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/validate-session', methods=['POST'])
def validate_session():
    """
    Validate session token and get current user data.
    
    Request Body:
        session_token (str): Session token to validate
    
    Returns:
        JSON: Validation result with user data and user type
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({
                'valid': False,
                'error': 'Request body is required'
            }), 400
        
        session_token = data.get('session_token', '').strip()
        if not session_token:
            return jsonify({
                'valid': False,
                'error': 'Session token is required'
            }), 400
        
        # Validate session
        result = auth_service.validate_session(session_token)
        
        if result['valid']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        logging.error(f"Error in validate_session endpoint: {e}")
        return jsonify({
            'valid': False,
            'error': 'Session validation failed'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout user and invalidate session.
    
    Request Body:
        session_token (str): Session token to invalidate
    
    Returns:
        JSON: Logout confirmation
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        session_token = data.get('session_token', '').strip()
        if not session_token:
            return jsonify({
                'success': False,
                'message': 'Session token is required'
            }), 400
        
        # Invalidate session
        success = auth_service.logout(session_token)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Logged out successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Logout failed'
            }), 400
    
    except Exception as e:
        logging.error(f"Error in logout endpoint: {e}")
        return jsonify({
            'success': False,
            'message': 'An internal error occurred'
        }), 500

@auth_bp.route('/user-info', methods=['GET'])
def get_user_info():
    """
    Get current user information from session token.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Returns:
        JSON: Current user data with user type
    """
    try:
        # Get session token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Authorization header required'
            }), 401
        
        session_token = auth_header.replace('Bearer ', '').strip()
        if not session_token:
            return jsonify({
                'error': 'Session token required'
            }), 401
        
        # Validate session and get user info
        result = auth_service.validate_session(session_token)
        
        if result['valid']:
            return jsonify({
                'success': True,
                'user': result['user'],
                'user_type': result['user_type']
            }), 200
        else:
            return jsonify({
                'error': 'Invalid or expired session'
            }), 401
    
    except Exception as e:
        logging.error(f"Error in get_user_info endpoint: {e}")
        return jsonify({
            'error': 'Failed to get user info'
        }), 500