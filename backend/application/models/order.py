from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from application import db

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False)
    total_amount = db.Column(Numeric(10, 2), nullable=False)
    status = db.Column(String, default='PENDING')  # e.g., PENDING, PAID, CANCELLED
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    status = db.Column(String, default='PENDING')

    # Relationship to OrderItems
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "total_amount": float(self.total_amount),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), nullable=False)
    quantity = db.Column(Integer, nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)  # unit price

    order = relationship("Order", back_populates="items")

    def to_dict(self):
        return {
            "id": str(self.id),
            "order_id": str(self.order_id),
            "product_id": str(self.product_id),
            "quantity": self.quantity,
            "price": float(self.price)
        }