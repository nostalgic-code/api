"""
Authentication API Module

This module provides RESTful API endpoints for user authentication
including password-based authentication, phone-based OTP authentication, 
session management, and new user registration for the multi-tenant system.

Key Features:
- Customer user registration with company validation
- Multi-user type authentication (CustomerUser and PlatformUser)
- Password-based authentication
- Phone number based authentication
- OTP generation and SMS delivery
- OTP verification and user authentication
- Session token management with user type tracking
- Role-based access control

Endpoints:
    POST /auth/register - Register new customer user
    POST /auth/login - Login with email and password
    POST /auth/send-otp - Send OTP to user's phone
    POST /auth/verify-otp - Verify OTP and authenticate user
    POST /auth/validate-session - Validate session token
    POST /auth/logout - Logout and invalidate session
    GET /auth/user-info - Get current user information

Author: Development Team
Version: 3.0
"""

from flask import Blueprint, request, jsonify
import logging
from ..services.auth_service import AuthService

# Create Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Initialize auth service
auth_service = AuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new customer user with soft validation.
    
    Request Body:
        {
            "full_name": "John Doe",
            "email": "john@company.com",
            "password": "securepassword123",
            "phone": "+27123456789",
            "customer_code": "CUST001",
            "customer_name": "ABC Company Ltd",
            "customer_account_number": "ACC12345"
        }
    
    Response:
        {
            "success": true,
            "message": "Registration successful. Your account is pending approval from your company administrator.",
            "user": {
                "id": 1,
                "name": "John Doe",
                "email": "john@company.com",
                "phone": "+27123456789",
                "role": "owner",
                "status": "pending",
                "customer_name": "ABC Company Ltd"
            }
        }
    
    Note: All users are created with OWNER role and RESTRICTED permissions by default.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        # Call the unified auth service to create customer user
        result = auth_service.create_customer_user(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            # Return appropriate status code based on error
            status_code = 400
            if result.get('error_code') in ['EMAIL_EXISTS', 'PHONE_EXISTS']:
                status_code = 409
            
            return jsonify(result), status_code
            
    except Exception as e:
        logging.error(f"Error in registration endpoint: {e}")
        return jsonify({
            'success': False,
            'message': 'An internal error occurred',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login with email and password.
    
    Request Body:
        {
            "email": "john@company.com",
            "password": "securepassword123"
        }
    
    Response:
        {
            "success": true,
            "message": "Authentication successful",
            "session_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "user_type": "customer_user",
            "user": {
                "id": 1,
                "name": "John Doe",
                "email": "john@company.com",
                "role": "owner",
                "customer": {...},
                "permissions": {...}
            }
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required',
                'error_code': 'MISSING_CREDENTIALS'
            }), 400
        
        # Authenticate with password
        result = auth_service.authenticate_with_password(email, password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            # Return appropriate status code based on error
            status_code = 401
            if result.get('error_code') == 'AUTH_ERROR':
                status_code = 500
            
            return jsonify(result), status_code
            
    except Exception as e:
        logging.error(f"Error in login endpoint: {e}")
        return jsonify({
            'success': False,
            'message': 'An internal error occurred',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """
    Send OTP to user's phone number.
    
    Now supports both CustomerUser and PlatformUser authentication.
    
    Request Body:
        {
            "phone": "+27123456789"
        }
    
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
            elif result.get('error_code') == 'INTERNAL_ERROR':
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
        {
            "phone": "+27123456789",
            "otp": "123456"
        }
    
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
            elif result.get('error_code') == 'INTERNAL_ERROR':
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
        {
            "session_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    
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
        {
            "session_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    
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