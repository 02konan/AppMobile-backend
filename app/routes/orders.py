import random
import string
from urllib.parse import quote

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..auth_utils import current_user
from ..extensions import db
from ..models import Live, Order, OrderItem, Product

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

ORDER_STATUSES = (
    "pending",
    "confirmed",
    "preparing",
    "ready",
    "picked_up",
    "delivering",
    "delivered",
    "refused",
    "cancelled",
)

# Statuts que le COMMERÇANT peut poser (partie « avant livraison »).
MERCHANT_SETTABLE = ("confirmed", "preparing", "ready", "refused")

# Statuts « livraison » gérés UNIQUEMENT par le livreur (via /deliveries).
DRIVER_ONLY = ("picked_up", "delivering", "delivered")

# Statuts terminaux : la commande n'évolue plus côté commerçant.
TERMINAL_STATUSES = ("delivered", "refused", "cancelled")


def _generate_order_number():
    return "DLV-" + "".join(random.choices(string.digits, k=6))


def _unique_order_number():
    number = _generate_order_number()
    while Order.query.filter_by(order_number=number).first() is not None:
        number = _generate_order_number()
    return number


def _whatsapp_url(shop, order, item):
    """Lien wa.me pré-rempli vers la boutique (paiement WhatsApp du MVP)."""
    if shop is None:
        return None
    raw = shop.whatsapp or shop.phone or ""
    number = "".join(ch for ch in raw if ch.isdigit())
    if not number:
        return None
    message = (
        f"Bonjour, je souhaite commander {item.product_name} "
        f"(x{item.quantity}) — commande {order.order_number} "
        f"présentée dans votre live DIVIX."
    )
    return f"https://wa.me/{number}?text={quote(message)}"


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
    user = current_user()
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify({"error": "Commande introuvable"}), 404
    # L'acheteur ou le commerçant propriétaire de la boutique peut consulter.
    is_buyer = order.user_id == user.id
    is_shop_owner = user.shop is not None and order.shop_id == user.shop.id
    if not (is_buyer or is_shop_owner):
        return jsonify({"error": "Accès refusé"}), 403
    return jsonify(order.to_dict())


@orders_bp.post("")
@jwt_required()
def place_order():
    """Commande d'un produit (typiquement acheté pendant un live)."""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    product_id = (data.get("productId") or "").strip()
    shipping_address = (data.get("shippingAddress") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    quantity = int(data.get("quantity") or 1)

    product = db.session.get(Product, product_id) if product_id else None
    if product is None or not product.is_active:
        return jsonify({"error": "Produit introuvable"}), 404
    if product.shop_id is None:
        return jsonify({"error": "Ce produit n'est rattaché à aucune boutique"}), 400
    if quantity < 1:
        return jsonify({"error": "Quantité invalide"}), 400
    if not shipping_address:
        return jsonify({"error": "Adresse de livraison requise"}), 400
    if product.stock < quantity:
        return jsonify({"error": "Stock insuffisant"}), 400

    live_id = data.get("liveId")
    if live_id is not None and db.session.get(Live, live_id) is None:
        live_id = None

    unit_price = float(product.price)
    subtotal = round(unit_price * quantity, 2)

    order = Order(
        order_number=_unique_order_number(),
        user_id=user_id,
        shop_id=product.shop_id,
        live_id=live_id,
        subtotal=subtotal,
        shipping_cost=0,
        total=subtotal,
        shipping_address=shipping_address,
        customer_phone=phone,
        payment_method="whatsapp",
        status="pending",
    )
    db.session.add(order)
    db.session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name=product.name,
        unit_price=product.price,
        quantity=quantity,
        selected_color=data.get("selectedColor"),
        selected_size=data.get("selectedSize"),
    )
    db.session.add(item)
    product.stock -= quantity  # réservation du stock

    db.session.commit()

    payload = order.to_dict()
    payload["whatsappUrl"] = _whatsapp_url(product.shop, order, item)
    return jsonify(payload), 201


@orders_bp.put("/<int:order_id>/status")
@jwt_required()
def update_status(order_id):
    user = current_user()
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify({"error": "Commande introuvable"}), 404

    new_status = (request.get_json(silent=True) or {}).get("status")
    if new_status not in ORDER_STATUSES:
        return jsonify({"error": "Statut invalide"}), 400

    is_shop_owner = user.shop is not None and order.shop_id == user.shop.id
    is_buyer = order.user_id == user.id

    if is_shop_owner:
        # Le commerçant gère uniquement la partie « avant livraison ».
        if new_status in DRIVER_ONLY:
            return (
                jsonify({"error": "Ce statut est géré par le livreur"}),
                403,
            )
        if new_status not in MERCHANT_SETTABLE:
            return (
                jsonify({"error": "Statut non autorisé pour le commerçant"}),
                400,
            )
        # Une fois la commande prise en charge par la livraison (ou terminée),
        # le commerçant ne peut plus la modifier.
        if order.status in DRIVER_ONLY or order.status in TERMINAL_STATUSES:
            return (
                jsonify(
                    {"error": "La commande est prise en charge par la livraison"}
                ),
                409,
            )
        order.status = new_status
    elif is_buyer and new_status == "cancelled" and order.status == "pending":
        order.status = "cancelled"
    else:
        return jsonify({"error": "Action non autorisée"}), 403

    db.session.commit()
    return jsonify(order.to_dict())
