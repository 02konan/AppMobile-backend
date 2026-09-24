"""Candidatures « Devenir livreur » (KYC) côté application mobile.

Un utilisateur soumet une demande (zone + véhicule + pièces d'identité).
La validation se fait côté admin. À l'approbation, le compte passe livreur.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..auth_utils import current_user
from ..extensions import db
from ..models import DriverApplication

driver_apps_bp = Blueprint(
    "driver_applications", __name__, url_prefix="/api/driver-applications"
)

VALID_ID_TYPES = ("cni", "passport")


@driver_apps_bp.get("/mine")
@jwt_required()
def my_application():
    user = current_user()
    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    app_ = (
        DriverApplication.query.filter_by(user_id=user.id)
        .order_by(DriverApplication.id.desc())
        .first()
    )
    return jsonify(app_.to_dict() if app_ else None)


@driver_apps_bp.post("")
@jwt_required()
def submit_application():
    user = current_user()
    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    if user.role == "driver":
        return jsonify({"error": "Vous êtes déjà livreur"}), 400

    data = request.get_json(silent=True) or {}
    plate_number = (data.get("plateNumber") or "").strip()
    id_type = (data.get("idType") or "").strip().lower()

    if not plate_number:
        return jsonify({"error": "Le numéro d'immatriculation est obligatoire"}), 400
    if id_type not in VALID_ID_TYPES:
        return jsonify({"error": "Type de pièce d'identité invalide"}), 400

    pending = DriverApplication.query.filter_by(
        user_id=user.id, status="pending"
    ).first()
    app_ = pending or DriverApplication(user_id=user.id)
    app_.city = (data.get("city") or "").strip() or None
    app_.plate_number = plate_number
    app_.vignette_url = (data.get("vignetteUrl") or "").strip() or None
    app_.insurance_url = (data.get("insuranceUrl") or "").strip() or None
    app_.id_type = id_type
    app_.id_front_url = (data.get("idFrontUrl") or "").strip() or None
    app_.id_back_url = (data.get("idBackUrl") or "").strip() or None
    app_.selfie_url = (data.get("selfieUrl") or "").strip() or None
    app_.terms_version = (data.get("termsVersion") or "").strip() or None
    app_.status = "pending"
    app_.review_note = None
    if pending is None:
        db.session.add(app_)

    db.session.commit()
    return jsonify(app_.to_dict()), 201
