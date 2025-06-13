from app import db
from datetime import datetime
from enum import Enum

class UserStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"

class UserRole(Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(15), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CUSTOMER, index=True)
    status = db.Column(db.Enum(UserStatus), nullable=False, default=UserStatus.PENDING, index=True)
    customer_code = db.Column(db.String(50), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # MySQL table options
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
            'email': self.email,
            'role': self.role.value if self.role else None,
            'status': self.status.value if self.status else None,
            'customer_code': self.customer_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def is_approved(self):
        return self.status == UserStatus.APPROVED
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def find_by_phone(phone):
        return User.query.filter_by(phone=phone).first()
    
    @staticmethod
    def get_approved_user_by_phone(phone):
        return User.query.filter_by(phone=phone, status=UserStatus.APPROVED).first()
    
    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def find_by_customer_code(customer_code):
        return User.query.filter_by(customer_code=customer_code).first()
    
    def __repr__(self):
        return f'<User {self.phone}: {self.name}>'