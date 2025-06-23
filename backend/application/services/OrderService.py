from application import db
from application.models.order import OrderItem, Order
from application.models.cart import Cart

class OrderService:
    def create_order(self, user_id: int):
        cart = Cart.query.filter_by(user_id=user_id, is_active=True).first()
        if not cart or not cart.items:
            raise Exception("Cart is empty")

        total = sum(item.quantity * float(item.price) for item in cart.items)
        order = Order(
            user_id=user_id,
            total_amount=total,
            status='PENDING'
        )
        db.session.add(order)
        db.session.flush()  # get order.id

        # Create order items
        for cart_item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.price
            )
            db.session.add(order_item)

        # Deactivate cart
        cart.is_active = False
        db.session.commit()
        return order.to_dict()

    def get_order(self, order_id: int):
        order = Order.query.get(order_id)
        return order.to_dict() if order else None