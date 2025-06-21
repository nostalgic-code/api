# backend/application/models/customer.py
from application import db
from datetime import datetime
from enum import Enum

class CustomerType(Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"

class CustomerStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    account_number = db.Column(db.String(100), index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    type = db.Column(db.Enum(CustomerType, values_callable=lambda x: [e.value for e in x]), 
                     nullable=False, default=CustomerType.COMPANY)
    status = db.Column(db.Enum(CustomerStatus, values_callable=lambda x: [e.value for e in x]), 
                       nullable=False, default=CustomerStatus.PENDING, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to customer users
    users = db.relationship('CustomerUser', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.customer_code}: {self.name}>'