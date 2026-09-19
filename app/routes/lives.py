from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from ..auth_utils import require_roles
from ..extensions import db
from ..models import Live, Product, live_products

lives_bp = Blueprint("lives", __name__, url_prefix="/api/lives")

# Ordre d'affichage : en direct d'abord, puis à venir, puis terminés.
_STATUS_ORDER = {"live": 0, "scheduled": 1, "ended": 2}


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _owned_live_or_error(user, live_id):
    """Retourne (live, None) si le live appartient au commerçant, sinon (None, réponse)."""
    live = db.session.get(Live, live_id)
    if live is None:
        return None, (jsonify({"error": "Live introuvable"}), 404)
    if user.shop is None or live.shop_id != user.shop.id:
        return None, (jsonify({"error": "Accès refusé"}), 403)
    return live, None


def _set_live_products(live, product_ids, shop_id):
    """Remplace la sélection de produits du live (uniquement ceux de la boutique)."""
    valid = (
        Product.query.filter(
            Product.id.in_(product_ids), Product.shop_id == shop_id
        ).all()
        if product_ids
        else []
    )
    valid_ids = {p.id for p in valid}
    ordered = [pid for pid in product_ids if pid in valid_ids]

    db.session.execute(
        live_products.delete().where(live_products.c.live_id == live.id)
    )
    for position, pid in enumerate(ordered):
        db.session.execute(
            live_products.insert().values(
                live_id=live.id, product_id=pid, position=position
            )
        )
    return ordered


# ------------------------------------------------------------
# Lecture (public)
# ------------------------------------------------------------
@lives_bp.get("")
def list_lives():
    query = Live.query
    status = request.args.get("status")
    if status in ("scheduled", "live", "ended"):
        query = query.filter_by(status=status)

    shop_id = request.args.get("shop")
    if shop_id:
        query = query.filter_by(shop_id=shop_id)

    lives = query.all()
    lives.sort(
        key=lambda lv: (
            _STATUS_ORDER.get(lv.status, 9),
            lv.scheduled_at or lv.created_at or datetime.min,
        )
    )
    return jsonify([lv.to_dict() for lv in lives])


@lives_bp.get("/<int:live_id>")
def get_live(live_id):
    live = db.session.get(Live, live_id)
    if live is None:
        return jsonify({"error": "Live introuvable"}), 404
    return jsonify(live.to_dict(with_products=True))


# ------------------------------------------------------------
# Gestion (commerçant)
# ------------------------------------------------------------
@lives_bp.post("")
@require_roles("merchant")
def create_live(user):
    if user.shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Le titre est obligatoire"}), 400

    live = Live(
        shop_id=user.shop.id,
        title=title,
        description=(data.get("description") or "").strip() or None,
        category=(data.get("category") or "").strip() or None,
        scheduled_at=_parse_dt(data.get("scheduledAt")),
        status="scheduled",
    )
    db.session.add(live)
    db.session.flush()

    _set_live_products(live, data.get("productIds") or [], user.shop.id)
    db.session.commit()
    return jsonify(live.to_dict(with_products=True)), 201


@lives_bp.post("/<int:live_id>/products")
@require_roles("merchant")
def set_products(user, live_id):
    live, error = _owned_live_or_error(user, live_id)
    if error:
        return error

    data = request.get_json(silent=True) or {}
    product_ids = data.get("productIds")
    if not isinstance(product_ids, list):
        return jsonify({"error": "productIds (liste) requis"}), 400

    _set_live_products(live, product_ids, user.shop.id)
    db.session.commit()
    return jsonify(live.to_dict(with_products=True))


@lives_bp.put("/<int:live_id>/current-product")
@require_roles("merchant")
def set_current_product(user, live_id):
    live, error = _owned_live_or_error(user, live_id)
    if error:
        return error

    data = request.get_json(silent=True) or {}
    product_id = data.get("productId")

    if product_id is None:
        live.current_product_id = None  # masquer le produit affiché
    else:
        selected_ids = {p.id for p in live.products}
        if product_id not in selected_ids:
            return (
                jsonify({"error": "Ce produit ne fait pas partie du live"}),
                400,
            )
        live.current_product_id = product_id

    db.session.commit()
    return jsonify(live.to_dict())


@lives_bp.post("/<int:live_id>/start")
@require_roles("merchant")
def start_live(user, live_id):
    live, error = _owned_live_or_error(user, live_id)
    if error:
        return error
    if live.status == "ended":
        return jsonify({"error": "Ce live est terminé"}), 400

    live.status = "live"
    live.started_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(live.to_dict())


@lives_bp.post("/<int:live_id>/end")
@require_roles("merchant")
def end_live(user, live_id):
    live, error = _owned_live_or_error(user, live_id)
    if error:
        return error

    live.status = "ended"
    live.ended_at = datetime.now(timezone.utc)
    live.current_product_id = None
    db.session.commit()
    return jsonify(live.to_dict())
