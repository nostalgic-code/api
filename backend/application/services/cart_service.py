from application import db
from application.models.cart import Cart, CartItem
from application.models.product import Product
import json

class CartService:
    def get_cart(self, user_id: int):
        cart = Cart.query.filter_by(customer_user_id=user_id, is_active=True).first()
        return cart.to_dict() if cart else None

    def add_to_cart(self, user_id: int, product_code: str, quantity: int):
        cart = Cart.query.filter_by(customer_user_id=user_id, is_active=True).first()
        if not cart:
            cart = Cart(customer_user_id=user_id, items=json.dumps([]))
            db.session.add(cart)
            db.session.flush()
        
        # Find product
        product = Product.query.filter_by(product_code=product_code).first()
        if not product:
            raise Exception("Product not found")
        
       # Check if item already in cart
        item = CartItem.query.filter_by(cart_id=cart.id, product_code=product_code).first()
        if item:
            item.quantity += quantity
        else:
            item = CartItem(
                cart_id=cart.id,
                product_code=product_code,
                product_name=product.name,
                quantity=quantity,
                price=product.current_price,
                depot_code=product.depot_code
            )
            db.session.add(item)
        db.session.commit()
        return cart.to_dict()

    def save_cart(self, user_id, items):
        cart = Cart.query.filter_by(customer_user_id=user_id, is_active=True).first()
        if not cart:
            cart = Cart(customer_user_id=user_id)
            db.session.add(cart)
            db.session.flush()
        CartItem.query.filter_by(cart_id=cart.id).delete()
        for item in items:
            product = Product.query.filter_by(product_code=item['product_code']).first()
            if not product:
                continue
            db.session.add(CartItem(
                cart_id=cart.id,
                product_code=product.product_code,
                product_name=product.name,
                quantity=item['quantity'],
                price=product.current_price,
                depot_code=product.depot_code
            ))
        db.session.commit()
        return cart.to_dict()