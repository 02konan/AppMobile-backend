import random
import string

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import CartItem, Order, OrderItem

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

FREE_SHIPPING_THRESHOLD = 50.0
SHIPPING_COST = 4.99
VALID_PAYMENT_METHODS = ("card", "paypal", "cash")


def _generate_order_number():
    return "CMD-" + "".join(random.choices(string.digits, k=6))


@orders_bp.get("")
@jwt_required()
def list_orders():
    user_id = int(get_jwt_identity())
    orders = (
        Order.query.filter_by(user_id=user_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return jsonify([o.to_dict() for o in orders])


@orders_bp.get("/<int:order_id>")
@jwt_required()
def get_order(order_id):
    user_id = int(get_jwt_identity())
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if order is None:
        return jsonify({"error": "Commande introuvable"}), 404
    return jsonify(order.to_dict())


@orders_bp.post("")
@jwt_required()
def place_order():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    shipping_address = (data.get("shippingAddress") or "").strip()
    payment_method = data.get("paymentMethod", "card")

    if not shipping_address:
        return jsonify({"error": "shippingAddress requis"}), 400
    if payment_method not in VALID_PAYMENT_METHODS:
        return jsonify({"error": "paymentMethod invalide"}), 400

    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({"error": "Le panier est vide"}), 400

    subtotal = round(
        sum(float(item.product.price) * item.quantity for item in cart_items), 2
    )
    shipping_cost = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_COST
    total = round(subtotal + shipping_cost, 2)

    order_number = _generate_order_number()
    while Order.query.filter_by(order_number=order_number).first() is not None:
        order_number = _generate_order_number()

    order = Order(
        order_number=order_number,
        user_id=user_id,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
        shipping_address=shipping_address,
        payment_method=payment_method,
        status="processing",
    )
    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name,
                unit_price=item.product.price,
                quantity=item.quantity,
                selected_color=item.selected_color,
                selected_size=item.selected_size,
            )
        )
        db.session.delete(item)

    db.session.commit()
    return jsonify(order.to_dict()), 201
