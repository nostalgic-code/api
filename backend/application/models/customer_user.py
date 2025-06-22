from datetime import datetime
from enum import Enum
from application import db

class CustomerUserRole(Enum):
    OWNER = "owner"
    STAFF = "staff"
    VIEWER = "viewer"

class CustomerUserStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class CustomerUser(db.Model):
    __tablename__ = 'customer_users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255)) # For password-based login if needed
    phone = db.Column(db.String(50), unique=True, index=True) # For OTP
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    role = db.Column(db.Enum(CustomerUserRole, values_callable=lambda x: [e.value for e in x]), 
                     default=CustomerUserRole.VIEWER, index=True)
    permission_code = db.Column(db.String(10), db.ForeignKey('permission_codes.code'), nullable=True)
    permissions = db.Column(db.JSON)
    depot_access = db.Column(db.JSON)
    status = db.Column(db.Enum(CustomerUserStatus, values_callable=lambda x: [e.value for e in x]), 
                       default=CustomerUserStatus.PENDING, index=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CustomerUser {self.email}>'