"""
Authentication API Module

This module provides RESTful API endpoints for user authentication
including phone-based OTP authentication and session management.

Key Features:
- Phone number based authentication
- OTP generation and SMS delivery
- OTP verification and user authentication
- Session token management
- Role-based access control

Endpoints:
    POST /auth/send-otp - Send OTP to user's phone
    POST /auth/verify-otp - Verify OTP and authenticate user
    POST /auth/validate-session - Validate session token
    POST /auth/logout - Logout and invalidate session

Dependencies:
    - Flask Blueprint for route organization
    - AuthService for authentication logic
    - Input validation utilities

Usage:
    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

Author: Development Team
Version: 1.0
"""

from flask import Blueprint, request, jsonify
import logging
from ..services.auth_service import AuthService

# Create Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Initialize auth service
auth_service = AuthService()

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """
    Send OTP to user's phone number.
    
    Request Body:
        phone (str): User's phone number
    
    Returns:
        JSON: Success/error response with OTP status
    
    Example Request:
        POST /auth/send-otp
        {
            "phone": "+27123456789"
        }
    
    Example Response:
        {
            "success": true,
            "message": "OTP sent to +27123456789",
            "expires_in": 300
        }
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
            if result.get('error_code') in ['USER_NOT_FOUND', 'USER_NOT_APPROVED']:
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
    
    Request Body:
        phone (str): User's phone number
        otp (str): OTP code to verify
    
    Returns:
        JSON: Authentication result with user data and session token
    
    Example Request:
        POST /auth/verify-otp
        {
            "phone": "+27123456789",
            "otp": "123456"
        }
    
    Example Response:
        {
            "success": true,
            "message": "Authentication successful",
            "user": {
                "id": 1,
                "phone": "+27123456789",
                "name": "John Doe",
                "role": "customer",
                "status": "approved"
            },
            "session_token": "abc123..."
        }
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
        JSON: Validation result with user data
    
    Example Request:
        POST /auth/validate-session
        {
            "session_token": "abc123..."
        }
    
    Example Response:
        {
            "valid": true,
            "user": {
                "id": 1,
                "phone": "+27123456789",
                "name": "John Doe",
                "role": "customer"
            }
        }
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
    
    Example Request:
        POST /auth/logout
        {
            "session_token": "abc123..."
        }
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
        
        # Invalidate session (implement in auth service)
        success = auth_service.logout(session_token)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Logged out successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Session not found or already expired'
            }), 404
    
    except Exception as e:
        logging.error(f"Error in logout endpoint: {e}")
        return jsonify({
            'success': False,
            'message': 'Logout failed'
        }), 500

@auth_bp.route('/user-info', methods=['GET'])
def get_user_info():
    """
    Get current user information from session token.
    
    Headers:
        Authorization: Bearer <session_token>
    
    Returns:
        JSON: Current user data
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
                'user': result['user']
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