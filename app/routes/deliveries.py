"""Livraisons DIVIX : prise en charge des commandes par les livreurs.

Flux : le commerçant marque une commande « ready » (prête). Elle devient
alors disponible pour les livreurs, qui peuvent la prendre en charge, puis
faire évoluer le statut (récupérée → en livraison → livrée). Chaque
changement synchronise le statut de la commande côté acheteur/commerçant.
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from ..auth_utils import current_user, require_roles
from ..extensions import db
from ..models import Delivery, Order, User

deliveries_bp = Blueprint("deliveries", __name__, url_prefix="/api/deliveries")

# Transitions autorisées côté livreur.
_DRIVER_TRANSITIONS = {
    "assigned": {"picked_up", "failed"},
    "picked_up": {"delivering", "failed"},
    "delivering": {"delivered", "failed"},
}


def _now():
    return datetime.now(timezone.utc)


def _delivery_payload(delivery):
    """Livraison + résumé de la commande, pour l'app livreur."""
    data = delivery.to_dict()
    order = delivery.order
    if order is not None:
        data["order"] = {
            "id": order.id,
            "orderNumber": order.order_number,
            "total": float(order.total),
            "status": order.status,
            "statusLabel": order.STATUS_LABELS.get(order.status, order.status),
            "shippingAddress": order.shipping_address,
            "customerName": order.user.name if order.user else None,
            "customerPhone": order.customer_phone
            or (order.user.phone if order.user else None),
            "shopName": order.shop.name if order.shop else None,
            "items": [
                {
                    "name": it.product_name,
                    "quantity": it.quantity,
                }
                for it in order.items
            ],
        }
    return data


# ------------------------------------------------------------
# Livreur
# ------------------------------------------------------------
@deliveries_bp.get("/available")
@require_roles("driver")
def available_deliveries(user):
    """Commandes prêtes, sans livreur affecté."""
    orders = (
        Order.query.filter(Order.status == "ready")
        .filter(~Order.delivery.has())
        .order_by(Order.updated_at.asc())
        .all()
    )
    result = []
    for order in orders:
        result.append(
            {
                "orderId": order.id,
                "orderNumber": order.order_number,
                "total": float(order.total),
                "shippingAddress": order.shipping_address,
                "customerName": order.user.name if order.user else None,
                "shopName": order.shop.name if order.shop else None,
                "commune": order.shop.commune if order.shop else None,
                "itemCount": len(order.items),
                "createdAt": order.created_at.isoformat()
                if order.created_at
                else None,
            }
        )
    return jsonify(result)


@deliveries_bp.get("/mine")
@require_roles("driver")
def my_deliveries(user):
    """Courses du livreur. ?history=1 pour inclure les terminées."""
    query = Delivery.query.filter_by(driver_id=user.id)
    if request.args.get("history") not in ("1", "true"):
        query = query.filter(Delivery.status.notin_(["delivered", "failed"]))
    deliveries = query.order_by(Delivery.updated_at.desc()).all()
    return jsonify([_delivery_payload(d) for d in deliveries])


@deliveries_bp.post("/claim/<int:order_id>")
@require_roles("driver")
def claim_delivery(user, order_id):
    """Le livreur prend en charge une commande prête."""
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify({"error": "Commande introuvable"}), 404
    if order.status != "ready":
        return jsonify({"error": "Cette commande n'est pas prête à être livrée"}), 400
    if order.delivery is not None:
        return jsonify({"error": "Commande déjà prise en charge"}), 409

    delivery = Delivery(
        order_id=order.id,
        driver_id=user.id,
        status="assigned",
        assigned_at=_now(),
    )
    db.session.add(delivery)
    db.session.commit()
    return jsonify(_delivery_payload(delivery)), 201


@deliveries_bp.get("/<int:delivery_id>")
@require_roles("driver", "merchant", "admin")
def get_delivery(user, delivery_id):
    delivery = db.session.get(Delivery, delivery_id)
    if delivery is None:
        return jsonify({"error": "Livraison introuvable"}), 404
    order = delivery.order
    is_driver = delivery.driver_id == user.id
    is_owner = (
        user.shop is not None and order is not None and order.shop_id == user.shop.id
    )
    if not (is_driver or is_owner or user.role == "admin"):
        return jsonify({"error": "Accès refusé"}), 403
    return jsonify(_delivery_payload(delivery))


@deliveries_bp.put("/<int:delivery_id>/status")
@require_roles("driver")
def update_delivery_status(user, delivery_id):
    delivery = db.session.get(Delivery, delivery_id)
    if delivery is None:
        return jsonify({"error": "Livraison introuvable"}), 404
    if delivery.driver_id != user.id:
        return jsonify({"error": "Cette livraison n'est pas la vôtre"}), 403

    new_status = (request.get_json(silent=True) or {}).get("status")
    allowed = _DRIVER_TRANSITIONS.get(delivery.status, set())
    if new_status not in allowed:
        return (
            jsonify(
                {
                    "error": "Transition de statut invalide",
                    "allowed": sorted(allowed),
                }
            ),
            400,
        )

    delivery.status = new_status
    if new_status == "picked_up":
        delivery.picked_up_at = _now()
    elif new_status == "delivered":
        delivery.delivered_at = _now()

    # Synchronise le statut de la commande.
    order = delivery.order
    if order is not None and new_status in Delivery.ORDER_STATUS_SYNC:
        order.status = Delivery.ORDER_STATUS_SYNC[new_status]

    db.session.commit()
    return jsonify(_delivery_payload(delivery))


# ------------------------------------------------------------
# Affectation manuelle (commerçant propriétaire ou admin)
# ------------------------------------------------------------
@deliveries_bp.post("/assign/<int:order_id>")
@require_roles("merchant", "admin")
def assign_delivery(user, order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify({"error": "Commande introuvable"}), 404
    if user.role != "admin" and (
        user.shop is None or order.shop_id != user.shop.id
    ):
        return jsonify({"error": "Accès refusé"}), 403

    driver_id = (request.get_json(silent=True) or {}).get("driverId")
    driver = db.session.get(User, driver_id) if driver_id else None
    if driver is None or driver.role != "driver":
        return jsonify({"error": "Livreur introuvable"}), 404

    delivery = order.delivery
    if delivery is None:
        delivery = Delivery(order_id=order.id)
        db.session.add(delivery)
    delivery.driver_id = driver.id
    delivery.status = "assigned"
    delivery.assigned_at = _now()
    db.session.commit()
    return jsonify(_delivery_payload(delivery))
