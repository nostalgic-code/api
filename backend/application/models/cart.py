from sqlalchemy import Column, String, Integer, ForeignKey, Numeric, DateTime, func
from application import db
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_user_id = db.Column(UUID(as_uuid=True), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now())
    is_active = db.Column(db.Boolean, default=True, index=True)
    

    # Relationship to CartItem
    items = relationship('CartItem', back_populates='cart', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.customer_user_id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "items": [item.to_dict() for item in self.items]
        }


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id = db.Column(UUID(as_uuid=True), ForeignKey('carts.id', ondelete='CASCADE'), nullable=False)
    product_code = db.Column(UUID(as_uuid=True), nullable=False)
    product_name = db.Column(String, nullable=False)
    quantity = db.Column(Integer, nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)
    depot_code = db.Column(String, nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to Cart
    cart = relationship('Cart', back_populates='items')

    def to_dict(self):
        return {
            "id": str(self.id),
            "cart_id": str(self.cart_id),
            "product_code": str(self.product_id),
            "product_name": str(self.product_name),
            "quantity": self.quantity,
            "price": float(self.price),
            "depot_code": str(self.depot_code),
            "created_at": self.created_at.isoformat(),
        }