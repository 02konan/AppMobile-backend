"""Candidatures « Devenir vendeur » (KYC) côté application mobile.

Un acheteur soumet une demande (boutique + visuels + pièces d'identité).
La validation se fait côté admin (panneau Flask). L'acheteur peut consulter
le statut de sa demande.
"""

from flask import Blueprint, jsonify, request

from ..auth_utils import current_user
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import SellerApplication

seller_apps_bp = Blueprint(
    "seller_applications", __name__, url_prefix="/api/seller-applications"
)

VALID_ID_TYPES = ("cni", "passport")


@seller_apps_bp.get("/mine")
@jwt_required()
def my_application():
    user = current_user()
    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    app_ = (
        SellerApplication.query.filter_by(user_id=user.id)
        .order_by(SellerApplication.id.desc())
        .first()
    )
    return jsonify(app_.to_dict() if app_ else None)


@seller_apps_bp.post("")
@jwt_required()
def submit_application():
    user = current_user()
    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    if user.role == "merchant" or user.shop is not None:
        return jsonify({"error": "Vous êtes déjà vendeur"}), 400

    data = request.get_json(silent=True) or {}
    shop_name = (data.get("shopName") or "").strip()
    id_type = (data.get("idType") or "").strip().lower()

    if not shop_name:
        return jsonify({"error": "Le nom de la boutique est obligatoire"}), 400
    if id_type not in VALID_ID_TYPES:
        return jsonify({"error": "Type de pièce d'identité invalide"}), 400

    # Une seule candidature en attente à la fois : on remplace la précédente.
    pending = SellerApplication.query.filter_by(
        user_id=user.id, status="pending"
    ).first()
    app_ = pending or SellerApplication(user_id=user.id)
    app_.shop_name = shop_name
    app_.category = (data.get("category") or "").strip() or None
    app_.city = (data.get("city") or "").strip() or None
    app_.logo_url = (data.get("logoUrl") or "").strip() or None
    app_.cover_url = (data.get("coverUrl") or "").strip() or None
    app_.id_type = id_type
    app_.id_front_url = (data.get("idFrontUrl") or "").strip() or None
    app_.id_back_url = (data.get("idBackUrl") or "").strip() or None
    app_.selfie_url = (data.get("selfieUrl") or "").strip() or None
    app_.status = "pending"
    app_.review_note = None
    if pending is None:
        db.session.add(app_)

    db.session.commit()
    return jsonify(app_.to_dict()), 201
