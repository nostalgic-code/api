from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, func, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from enum import Enum
from datetime import datetime

from application import db

class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User information
    user_id = db.Column(UUID(as_uuid=True), nullable=False)
    customer_id = db.Column(db.Integer, nullable=True)  # Link to customer table
    customer_user_id = db.Column(db.Integer, nullable=True)  # Link to customer_user table
    
    # Order details
    order_number = db.Column(db.String(50), unique=True, nullable=True, index=True)
    p_number = db.Column(db.String(50), unique=True, nullable=True, index=True)
    external_reference = db.Column(db.String(50), nullable=True)
    
    # Financial details
    total_amount = db.Column(Numeric(10, 2), nullable=False)
    vat_amount = db.Column(Numeric(10, 2), nullable=True, default=0.00)
    
    # Status tracking
    status = db.Column(SQLEnum(OrderStatus, values_callable=lambda x: [e.value for e in x], native_enum=False), 
                      nullable=False, default=OrderStatus.PENDING, index=True)
    
    # Timestamps
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to OrderItems
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "customer_id": self.customer_id,
            "customer_user_id": self.customer_user_id,
            "order_number": self.order_number,
            "p_number": self.p_number,
            "external_reference": self.external_reference,
            "total_amount": float(self.total_amount),
            "vat_amount": float(self.vat_amount) if self.vat_amount is not None else 0.0,
            "status": self.status.value if hasattr(self.status, "value") else self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    
    # Product details
    product_id = db.Column(UUID(as_uuid=True), nullable=True)
    product_code = db.Column(db.String(50), nullable=False, index=True)
    product_name = db.Column(db.String(255), nullable=True)
    quantity = db.Column(Integer, nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)  # unit price
    vat = db.Column(Numeric(10, 2), nullable=True, default=0.00)
    
    # Timestamps
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="items")

    def to_dict(self):
        return {
            "id": str(self.id),
            "order_id": str(self.order_id),
            "product_id": str(self.product_id) if self.product_id else None,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "price": float(self.price),
            "vat": float(self.vat) if self.vat is not None else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }