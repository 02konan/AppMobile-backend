"""Enregistrement des appareils pour les notifications push (FCM)."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import DeviceToken

devices_bp = Blueprint("devices", __name__, url_prefix="/api/devices")


@devices_bp.post("")
@jwt_required()
def register_device():
    """Enregistre (ou réaffecte) un jeton FCM à l'utilisateur connecté."""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    if not token:
        return jsonify({"error": "token requis"}), 400
    platform = (data.get("platform") or "").strip()[:20] or None

    existing = DeviceToken.query.filter_by(token=token).first()
    if existing is None:
        db.session.add(
            DeviceToken(user_id=user_id, token=token, platform=platform)
        )
    else:
        existing.user_id = user_id
        if platform:
            existing.platform = platform
    db.session.commit()
    return jsonify({"ok": True}), 201


@devices_bp.delete("")
@jwt_required()
def unregister_device():
    """Supprime un jeton (déconnexion / désactivation des notifications)."""
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    if token:
        DeviceToken.query.filter_by(token=token).delete(
            synchronize_session=False
        )
        db.session.commit()
    return jsonify({"ok": True})
