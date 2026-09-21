"""Signalements : un utilisateur signale un contenu abusif (produit, live,
boutique, utilisateur). Les signalements sont traités depuis le panneau
d'administration."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..auth_utils import current_user
from ..extensions import db
from ..models import Report

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

_TARGET_TYPES = ("product", "live", "shop", "user")


@reports_bp.post("")
@jwt_required()
def create_report():
    user = current_user()
    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404

    data = request.get_json(silent=True) or {}
    target_type = (data.get("targetType") or "").strip()
    target_id = str(data.get("targetId") or "").strip()
    reason = (data.get("reason") or "").strip()
    message = (data.get("message") or "").strip() or None

    if target_type not in _TARGET_TYPES:
        return jsonify({"error": "Type de contenu invalide"}), 400
    if not target_id:
        return jsonify({"error": "Contenu ciblé requis"}), 400
    if not reason:
        return jsonify({"error": "Motif requis"}), 400

    report = Report(
        reporter_id=user.id,
        target_type=target_type,
        target_id=target_id[:30],
        reason=reason[:100],
        message=message[:1000] if message else None,
        status="open",
    )
    db.session.add(report)
    db.session.commit()
    return jsonify(report.to_dict()), 201


@reports_bp.get("/mine")
@jwt_required()
def my_reports():
    user = current_user()
    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    reports = (
        Report.query.filter_by(reporter_id=user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in reports])
