from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import CartItem, Product

cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")

FREE_SHIPPING_THRESHOLD = 50.0
SHIPPING_COST = 4.99


def _cart_summary(user_id):
    items = CartItem.query.filter_by(user_id=user_id).all()
    items_dicts = [item.to_dict() for item in items]
    subtotal = round(sum(item["totalPrice"] for item in items_dicts), 2)
    shipping_cost = 0.0 if subtotal == 0 or subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_COST
    return {
        "items": items_dicts,
        "itemCount": sum(item["quantity"] for item in items_dicts),
        "subtotal": subtotal,
        "shippingCost": shipping_cost,
        "total": round(subtotal + shipping_cost, 2),
    }


@cart_bp.get("")
@jwt_required()
def get_cart():
    return jsonify(_cart_summary(int(get_jwt_identity())))


@cart_bp.post("")
@jwt_required()
def add_to_cart():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    product_id = data.get("productId")
    color = data.get("selectedColor")
    size = data.get("selectedSize")

    try:
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 0

    if not product_id or quantity < 1:
        return jsonify({"error": "productId et quantity (>=1) requis"}), 400

    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify({"error": "Produit introuvable"}), 404

    item = CartItem.query.filter_by(
        user_id=user_id,
        product_id=product_id,
        selected_color=color,
        selected_size=size,
    ).first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            selected_color=color,
            selected_size=size,
        )
        db.session.add(item)

    db.session.commit()
    return jsonify(_cart_summary(user_id)), 201


@cart_bp.put("/<int:item_id>")
@jwt_required()
def update_cart_item(item_id):
    user_id = int(get_jwt_identity())
    item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if item is None:
        return jsonify({"error": "Article introuvable"}), 404

    data = request.get_json(silent=True) or {}
    try:
        quantity = int(data.get("quantity"))
    except (TypeError, ValueError):
        quantity = None

    if quantity is None or quantity < 1:
        return jsonify({"error": "quantity (>=1) requis"}), 400

    item.quantity = quantity
    db.session.commit()
    return jsonify(_cart_summary(user_id))


@cart_bp.delete("/<int:item_id>")
@jwt_required()
def remove_cart_item(item_id):
    user_id = int(get_jwt_identity())
    item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if item is not None:
        db.session.delete(item)
        db.session.commit()
    return jsonify(_cart_summary(user_id))


@cart_bp.delete("")
@jwt_required()
def clear_cart():
    user_id = int(get_jwt_identity())
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify(_cart_summary(user_id))
