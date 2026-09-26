import os
import json
import re
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Shop, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

VALID_ROLES = ("buyer", "merchant", "driver")

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")


def _firebase_admin_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            raise RuntimeError("Firebase Admin n'est pas configuré")
        service_account = json.loads(service_account_json)
        return firebase_admin.initialize_app(credentials.Certificate(service_account))


def _normalize_username(value):
    return (value or "").strip().lower()


# ------------------------------------------------------------
# Disponibilité du nom d'utilisateur
# ------------------------------------------------------------
@auth_bp.get("/check-username")
def check_username():
    username = _normalize_username(request.args.get("username"))
    if not USERNAME_RE.match(username):
        return jsonify(
            {
                "available": False,
                "reason": "3 à 30 caractères : lettres, chiffres, _",
            }
        )
    taken = User.query.filter_by(username=username).first() is not None
    return jsonify({"available": not taken, "username": username})


# ------------------------------------------------------------
# Inscription
# ------------------------------------------------------------
@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or "buyer").strip()
    email = (data.get("email") or "").strip().lower() or None
    firebase_id_token = (data.get("firebaseIdToken") or "").strip()
    username = _normalize_username(data.get("username")) or None
    country = (data.get("country") or "").strip() or None
    city = (data.get("city") or "").strip() or None
    otp_code = (data.get("otpCode") or "").strip()

    if not name or not phone or len(password) < 8:
        return (
            jsonify(
                {
                    "error": "Nom, téléphone et mot de passe (min. 8 caractères) requis"
                }
            ),
            400,
        )

    if role not in VALID_ROLES:
        return jsonify({"error": "Type de compte invalide"}), 400

    if username is not None and not USERNAME_RE.match(username):
        return jsonify({"error": "Nom d'utilisateur invalide"}), 400

    if not firebase_id_token:
        return jsonify({"error": "Vérification du téléphone requise"}), 400
    try:
        firebase_user = firebase_auth.verify_id_token(
            firebase_id_token,
            app=_firebase_admin_app(),
        )
    except RuntimeError:
        return jsonify({"error": "La vérification Firebase n'est pas configurée"}), 503
    except Exception:
        return jsonify({"error": "Jeton Firebase invalide ou expiré"}), 401

    if firebase_user.get("phone_number") != phone:
        return jsonify({"error": "Le numéro vérifié ne correspond pas"}), 403

    if User.query.filter_by(phone=phone).first() is not None:
        return jsonify({"error": "Un compte existe déjà avec ce téléphone"}), 409

    if username and User.query.filter_by(username=username).first() is not None:
        return jsonify({"error": "Ce nom d'utilisateur est déjà pris"}), 409

    if email and User.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "Un compte existe déjà avec cet e-mail"}), 409

    user = User(
        name=name,
        username=username,
        phone=phone,
        email=email,
        role=role,
        country=country,
        city=city,
        phone_verified=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # pour obtenir user.id

    # Un commerçant obtient automatiquement une boutique (à compléter ensuite).
    if role == "merchant":
        shop_name = (data.get("shopName") or "").strip() or f"Boutique de {name}"
        shop = Shop(user_id=user.id, name=shop_name, whatsapp=phone, phone=phone)
        db.session.add(shop)

    db.session.commit()

    token = create_access_token(identity=str(user.id))
    payload = {"token": token, "user": user.to_dict()}
    if user.shop is not None:
        payload["shop"] = user.shop.to_dict()
    return jsonify(payload), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = None
    if phone:
        digits = re.sub(r"\D", "", phone)
        candidates = [phone, digits]
        if not phone.startswith("+"):
            candidates.append(f"+225{digits}")
        for candidate in dict.fromkeys(candidates):
            user = User.query.filter_by(phone=candidate).first()
            if user is not None:
                break
    if user is None and email:
        user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({"error": "Téléphone ou mot de passe incorrect"}), 401

    token = create_access_token(identity=str(user.id))
    payload = {"token": token, "user": user.to_dict()}
    if user.shop is not None:
        payload["shop"] = user.shop.to_dict()
    return jsonify(payload)


@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    payload = user.to_dict()
    if user.shop is not None:
        payload["shop"] = user.shop.to_dict()
    return jsonify(payload)


@auth_bp.put("/me")
@jwt_required()
def update_me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404

    data = request.get_json(silent=True) or {}
    if data.get("name"):
        user.name = data["name"].strip()
    if "address" in data:
        user.address = data["address"]
    if "phone" in data:
        user.phone = data["phone"]
    if "city" in data:
        user.city = (data["city"] or "").strip() or None
    if "country" in data:
        user.country = (data["country"] or "").strip() or None

    db.session.commit()
    return jsonify(user.to_dict())
