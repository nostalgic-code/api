"""
Authentication Service Helper Functions

This module contains helper functions used by the AuthService class.

Functions:
    find_user_by_phone: Find user in either CustomerUser or PlatformUser table
    validate_customer_user_status: Validate customer user and their parent customer status
    build_customer_user_payload: Build enhanced payload for customer users
    build_platform_user_payload: Build payload for platform users
    calculate_effective_permissions: Calculate effective permissions by merging default and custom
    validate_phone: Validate phone number format
    validate_email: Validate email format
    send_sms: Send SMS with OTP using BulkSMS service
    generate_session_token: Generate secure session token
    generate_otp: Generate a random OTP code
    hash_otp: Hash OTP for secure storage

Author: Development Team
Version: 1.0
"""

import re
import random
import string
import hashlib
import secrets
import logging
from typing import Dict, Optional, Union

from application.models.customer_user import CustomerUser, CustomerUserStatus
from application.models.platform_user import PlatformUser
from application.models.permission_code import PermissionCode
from application.services.sms_service import sms_service

logger = logging.getLogger(__name__)


def find_user_by_phone(phone: str) -> tuple[Optional[Union[CustomerUser, PlatformUser]], Optional[str]]:
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


def validate_customer_user_status(user: CustomerUser) -> Dict:
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


def build_customer_user_payload(user: CustomerUser) -> Dict:
    """Build enhanced payload for customer users"""
    # Get effective permissions
    effective_permissions = calculate_effective_permissions(user)
    
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


def build_platform_user_payload(user: PlatformUser) -> Dict:
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


def calculate_effective_permissions(user: CustomerUser) -> Dict:
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


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    pattern = r'^(\+27|0)[0-9]{9}$'
    return bool(re.match(pattern, phone))


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def send_sms(phone: str, otp: str, otp_length: int = 6) -> bool:
    """Send SMS with OTP using BulkSMS service"""
    try:
        # Log OTP to console for development
        logger.warning(f"=== OTP FOR DEVELOPMENT ===")
        logger.warning(f"Phone: {phone}")
        logger.warning(f"OTP Code: {otp}")
        logger.warning(f"===========================")
        
        # Try to send SMS but don't fail if it doesn't work
        try:
            success = sms_service.send_otp(phone, otp)
            if success:
                logger.info(f"SMS sent successfully to {phone}")
            else:
                logger.warning(f"SMS service failed for {phone}, but OTP is logged above")
        except Exception as sms_error:
            logger.warning(f"SMS service error for {phone}: {sms_error}, but OTP is logged above")
        
        # Always return True in development so the flow continues
        return True
        
    except Exception as e:
        logger.error(f"Error in send_sms for {phone}: {e}")
        return False


def generate_session_token() -> str:
    """Generate secure session token"""
    return secrets.token_urlsafe(32)


def generate_otp(otp_length: int = 6) -> str:
    """Generate a random OTP code."""
    return ''.join(random.choices(string.digits, k=otp_length))


def hash_otp(otp: str) -> str:
    """Hash OTP for secure storage."""
    return hashlib.sha256(otp.encode()).hexdigest()
