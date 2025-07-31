# backend/application/models/platform_user.py
from application import db
from datetime import datetime
from enum import Enum

class PlatformUserRole(Enum):
    ADMIN = "admin"
    SUPPORT = "support"
    DEVELOPER = "developer"

class PlatformUser(db.Model):
    __tablename__ = 'platform_users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(50), unique=True, nullable=True, index=True)  # For OTP
    password = db.Column(db.String(255))  # For future password-based auth
    role = db.Column(db.Enum(PlatformUserRole, values_callable=lambda x: [e.value for e in x]), 
                     nullable=False, default=PlatformUserRole.SUPPORT)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    def __repr__(self):
        return f'<PlatformUser {self.email}>'