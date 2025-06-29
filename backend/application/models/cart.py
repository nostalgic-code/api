from sqlalchemy import String, Integer, ForeignKey, Numeric, DateTime, func
from sqlalchemy import Enum as SqlEnum
from application import db
from sqlalchemy.orm import relationship
from enum import Enum

class CartStatus(Enum):
    ACTIVE = "ACTIVE"
    SUBMITTED = "SUBMITTED"
    SAVED = "SAVED"

class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    customer_user_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), server_default=func.now())
    status = db.Column(SqlEnum(CartStatus, name="cart_status", native_enum=False), 
                   default=CartStatus.ACTIVE, 
                   nullable=False)
    


    # Relationship to CartItem
    items = relationship('CartItem', back_populates='cart', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.customer_user_id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.created_at.isoformat(),
            "status": self.status.value,
            "items": [item.to_dict() for item in self.items]
        }


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, ForeignKey('carts.id', ondelete='CASCADE'), nullable=False)
    product_code = db.Column(db.Integer, nullable=False)
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
            "product_code": str(self.product_code),
            "product_name": str(self.product_name),
            "quantity": self.quantity,
            "price": float(self.price),
            "depot_code": str(self.depot_code),
            "created_at": self.created_at.isoformat(),
        }