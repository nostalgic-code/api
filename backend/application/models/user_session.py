# backend/application/models/user_session.py
from application import db
from datetime import datetime

class UserSession(db.Model):
    __tablename__ = 'user_sessions'  # Using generic name for polymorphic support
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    user_type = db.Column(db.String(20), nullable=False)  # 'customer_user' or 'platform_user'
    session_token = db.Column(db.String(64), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # No direct relationship - will be resolved dynamically based on user_type
    
    __table_args__ = (
        db.Index('idx_user_session_lookup', 'user_id', 'user_type'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci'
        }
    )
    
    @property
    def user(self):
        """Dynamically get the user based on user_type"""
        if self.user_type == 'customer_user':
            from application.models.customer_user import CustomerUser
            return CustomerUser.query.get(self.user_id)
        elif self.user_type == 'platform_user':
            from application.models.platform_user import PlatformUser
            return PlatformUser.query.get(self.user_id)
        return None