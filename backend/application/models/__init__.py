"""
Models Package

Import all models in the correct order to ensure proper foreign key resolution.
"""

# Import models without foreign keys first
from .depot import Depot
from .permission_code import PermissionCode
from .customer import Customer  # This was missing!

# Import models with foreign keys to above models
from .customer_user import CustomerUser
from .platform_user import PlatformUser

# Import models that depend on user models
from .user_otp import UserOTP
from .user_session import UserSession

# Import other models
from .product import Product

# Export all models
__all__ = [
    'Depot',
    'PermissionCode', 
    'Customer',  # Added
    'CustomerUser',
    'PlatformUser',
    'UserOTP',
    'UserSession',
    'Product',
]