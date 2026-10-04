"""ReelShops : vidéos courtes shoppables (façon TikTok).

Un reel appartient à une boutique. Il contient une vidéo (≤ 30 s, hébergée
sur Cloudinary) et une sélection de produits présentés en dessous, avec un
bouton « Acheter » côté acheteur (même parcours de commande que les lives).
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..auth_utils import require_roles
from ..extensions import db
from ..models import Product, Reel, reel_products
from ..push import notify_all

reels_bp = Blueprint("reels", __name__, url_prefix="/api/reels")


def _owned_reel_or_error(user, reel_id):
    reel = db.session.get(Reel, reel_id)
    if reel is None:
        return None, (jsonify({"error": "Reel introuvable"}), 404)
    if user.shop is None or reel.shop_id != user.shop.id:
        return None, (jsonify({"error": "Accès refusé"}), 403)
    return reel, None


def _set_reel_products(reel, product_ids, shop_id):
    """Remplace la sélection de produits du reel (uniquement ceux de la boutique)."""
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
        reel_products.delete().where(reel_products.c.reel_id == reel.id)
    )
    for position, pid in enumerate(ordered):
        db.session.execute(
            reel_products.insert().values(
                reel_id=reel.id, product_id=pid, position=position
            )
        )
    return ordered


# ------------------------------------------------------------
# Lecture (public)
# ------------------------------------------------------------
@reels_bp.get("")
def list_reels():
    """Feed des reels, du plus récent au plus ancien.

    Filtres : ?shop=<id> (reels d'une boutique).
    Pagination : ?limit (défaut 20, max 50) et ?before=<id> (reels plus
    anciens que cet identifiant), pour un défilement infini côté app.
    """
    query = Reel.query.filter_by(is_active=True)

    shop_id = request.args.get("shop", type=int)
    if shop_id:
        query = query.filter_by(shop_id=shop_id)

    before = request.args.get("before", type=int)
    if before:
        query = query.filter(Reel.id < before)

    limit = request.args.get("limit", default=20, type=int)
    limit = max(1, min(limit, 50))

    reels = query.order_by(Reel.id.desc()).limit(limit).all()
    return jsonify([r.to_dict() for r in reels])


@reels_bp.get("/<int:reel_id>")
def get_reel(reel_id):
    reel = db.session.get(Reel, reel_id)
    if reel is None or not reel.is_active:
        return jsonify({"error": "Reel introuvable"}), 404
    return jsonify(reel.to_dict())


@reels_bp.post("/<int:reel_id>/view")
def register_view(reel_id):
    """Incrémente le compteur de vues d'un reel (appelé à l'affichage)."""
    reel = db.session.get(Reel, reel_id)
    if reel is None or not reel.is_active:
        return jsonify({"error": "Reel introuvable"}), 404
    reel.view_count = (reel.view_count or 0) + 1
    db.session.commit()
    return jsonify({"viewCount": reel.view_count})


# ------------------------------------------------------------
# Gestion (commerçant)
# ------------------------------------------------------------
@reels_bp.get("/mine")
@require_roles("merchant")
def my_reels(user):
    if user.shop is None:
        return jsonify([])
    reels = (
        Reel.query.filter_by(shop_id=user.shop.id)
        .order_by(Reel.id.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in reels])


@reels_bp.post("")
@require_roles("merchant")
def create_reel(user):
    if user.shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404

    data = request.get_json(silent=True) or {}
    video_url = (data.get("videoUrl") or "").strip()
    if not video_url:
        return jsonify({"error": "La vidéo est obligatoire"}), 400

    duration = data.get("durationSeconds")
    try:
        duration = int(duration) if duration is not None else None
    except (TypeError, ValueError):
        duration = None
    if duration is not None and duration > Reel.MAX_DURATION_SECONDS + 1:
        return (
            jsonify(
                {
                    "error": "La vidéo ne doit pas dépasser "
                    f"{Reel.MAX_DURATION_SECONDS} secondes"
                }
            ),
            400,
        )

    reel = Reel(
        shop_id=user.shop.id,
        caption=(data.get("caption") or "").strip() or None,
        video_url=video_url,
        thumbnail_url=(data.get("thumbnailUrl") or "").strip() or None,
        duration_seconds=duration,
        is_active=True,
    )
    db.session.add(reel)
    db.session.flush()

    _set_reel_products(reel, data.get("productIds") or [], user.shop.id)
    db.session.commit()

    # Notifie tout le monde (sauf le commerçant) de la nouvelle vidéo.
    shop_name = user.shop.name if user.shop else "Une boutique"
    notify_all(
        "Nouveau ReelShop",
        f"{shop_name} vient de publier une vidéo.",
        data={"type": "reel", "reelId": reel.id},
        exclude_user_id=user.id,
    )
    return jsonify(reel.to_dict()), 201


@reels_bp.put("/<int:reel_id>")
@require_roles("merchant")
def update_reel(user, reel_id):
    reel, error = _owned_reel_or_error(user, reel_id)
    if error:
        return error

    data = request.get_json(silent=True) or {}
    if "caption" in data:
        reel.caption = (data.get("caption") or "").strip() or None
    if "isActive" in data:
        reel.is_active = bool(data.get("isActive"))
    if "productIds" in data and isinstance(data.get("productIds"), list):
        _set_reel_products(reel, data.get("productIds"), user.shop.id)

    db.session.commit()
    return jsonify(reel.to_dict())


@reels_bp.delete("/<int:reel_id>")
@require_roles("merchant")
def delete_reel(user, reel_id):
    reel, error = _owned_reel_or_error(user, reel_id)
    if error:
        return error
    db.session.execute(
        reel_products.delete().where(reel_products.c.reel_id == reel.id)
    )
    db.session.delete(reel)
    db.session.commit()
    return jsonify({"ok": True})
