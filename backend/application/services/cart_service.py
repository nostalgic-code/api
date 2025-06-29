from application import db
from application.models.cart import Cart, CartItem
from application.models.product import Product
from application.models.cart import CartStatus
from application.models.customer_user import CustomerUser
import json

class CartService:
    def get_cart(self, user_id: int):
        """Get complete cart for user"""
        cart = Cart.query.filter_by(customer_user_id=user_id, status=CartStatus.ACTIVE).first()
        return cart.to_dict() if cart else None
    
    def get_cart_item(self, user_id: str, product_code: str):
        """Get specific cart item"""
        cart = Cart.query.filter_by(customer_user_id=user_id, status=CartStatus.ACTIVE).first()
        if not cart:
            return None
        
        item = CartItem.query.filter_by(cart_id=cart.id, product_code=product_code).first()
        return item.to_dict() if item else None
    

    def save_cart_item(self, user_id: str, product_code: str, quantity: int):
        """Add or update cart item"""
        try:
            # Get or create cart
            cart = Cart.query.filter_by(customer_user_id=user_id, status=CartStatus.ACTIVE).first()
            if not cart:
                cart = Cart(customer_user_id=user_id, items=json.dumps([]))
                db.session.add(cart)
                db.session.flush()

            # Find product
            product = Product.query.filter_by(product_code=product_code).first()
            if not product:
                return {'success': False, 'message': 'Product not found'}

            # Check if item already in cart
            item = CartItem.query.filter_by(cart_id=cart.id, product_code=product_code).first()
            if item:
                item.quantity = quantity
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
            return {'success': True, 'data': item.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}

    def get_cart_item_count(self, user_id: str):
        """Get total item count in cart"""
        cart = Cart.query.filter_by(customer_user_id=user_id, status=CartStatus.ACTIVE).first()
        if not cart:
            return 0
        
        total = db.session.query(db.func.sum(CartItem.quantity)).filter_by(cart_id=cart.id).scalar()
        return total or 0

    def add_to_cart(self, user_id: str, product_code: str, quantity: int):
        """Add item to cart (incremental)"""
        try:
            # Get the user to access their depot_code
            user = CustomerUser.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Extract depot_code from user's depot_access JSON
            depot_code = None
            if user.depot_access and isinstance(user.depot_access, list) and len(user.depot_access) > 0:
                depot_code = user.depot_access[0]

            if not depot_code:
                return {'success': False, 'message': 'User depot access not configured'}
            

            cart = Cart.query.filter_by(customer_user_id=user_id, status=CartStatus.ACTIVE).first()
            if not cart:
                cart = Cart(customer_user_id=user_id, status=CartStatus.ACTIVE)
                db.session.add(cart)
                db.session.flush()

            # Find product
            product = Product.query.filter_by(product_code=product_code).first()
            if not product:
                return {'success': False, 'message': 'Product not found'}

            # Check if item already in cart
            item = CartItem.query.filter_by(cart_id=cart.id, product_code=product_code).first()
            if item:
                item.quantity += quantity
            else:
                item = CartItem(
                    cart_id=cart.id,
                    product_code=product_code,
                    product_name=product.description,
                    quantity=quantity,
                    price=product.current_price,
                    depot_code=depot_code
                )
                db.session.add(item)

            db.session.commit()
            return {'success': True, 'data': cart.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}

    def remove_cart_item(self, user_id: str, product_code: str):
        """Remove specific item from cart"""
        try:
            cart = Cart.query.filter_by(customer_user_id=user_id, status=CartStatus.ACTIVE).first()
            if not cart:
                return {'success': False, 'message': 'Cart not found'}

            item = CartItem.query.filter_by(cart_id=cart.id, product_code=product_code).first()
            if not item:
                return {'success': False, 'message': 'Item not found in cart'}

            db.session.delete(item)
            db.session.commit()
            return {'success': True, 'message': 'Item removed from cart'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}

    def clear_cart(self, user_id: str):
        """Clear entire cart"""
        try:
            cart = Cart.query.filter_by(customer_user_id=user_id, status=CartStatus.ACTIVE).first()
            if not cart:
                return {'success': False, 'message': 'Cart not found'}

            CartItem.query.filter_by(cart_id=cart.id).delete()
            db.session.commit()
            return {'success': True, 'message': 'Cart cleared successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}

    def save_cart(self, user_id: str, items):
        """Save entire cart from items list"""
        try:
            cart = Cart.query.filter_by(customer_user_id=user_id, is_active=True).first()
            if not cart:
                cart = Cart(customer_user_id=user_id)
                db.session.add(cart)
                db.session.flush()

            # Clear existing items
            CartItem.query.filter_by(cart_id=cart.id).delete()

            # Add new items
            for item_data in items:
                product = Product.query.filter_by(product_code=item_data['product_code']).first()
                if not product:
                    continue

                item = CartItem(
                    cart_id=cart.id,
                    product_code=product.product_code,
                    product_name=product.description,
                    quantity=item_data['quantity'],
                    price=product.current_price,
                    depot_code=product.depot_code
                )
                db.session.add(item)

            db.session.commit()
            return {'success': True, 'data': cart.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}

    def update_cart_item(self, user_id: str, product_code: str, quantity: int):
        """Update cart item quantity"""
        try:
            cart = Cart.query.filter_by(customer_user_id=user_id, status=CartStatus.ACTIVE).first()
            if not cart:
                return {'success': False, 'message': 'Cart not found'}

            item = CartItem.query.filter_by(cart_id=cart.id, product_code=product_code).first()
            if not item:
                return {'success': False, 'message': 'Item not found in cart'}

            if quantity == 0:
                db.session.delete(item)
                message = 'Item removed from cart'
            else:
                item.quantity = quantity
                message = 'Item quantity updated'

            db.session.commit()
            return {'success': True, 'message': message}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}


