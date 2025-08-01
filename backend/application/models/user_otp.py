# backend/application/models/user_otp.py
from application import db
from datetime import datetime

class UserOTP(db.Model):
    __tablename__ = 'customer_user_otps' # <-- Renamed table for clarity
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), nullable=False, index=True)
    otp_hash = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }