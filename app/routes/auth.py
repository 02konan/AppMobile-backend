import os
import random
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..extensions import db
from ..models import PhoneOtp, Shop, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

VALID_ROLES = ("buyer", "merchant", "driver")

# Envoi réel de SMS ? Tant qu'aucun fournisseur n'est configuré, on reste en
# mode « simulé » : le code n'est pas envoyé mais renvoyé à l'app (devCode)
# pour permettre les tests. Passer SMS_ENABLED=true quand un fournisseur
# (Twilio…) sera branché dans _send_sms().
SMS_ENABLED = os.environ.get("SMS_ENABLED", "false").lower() == "true"
OTP_TTL_MINUTES = 10
USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")


def _now():
    return datetime.now(timezone.utc)


def _normalize_username(value):
    return (value or "").strip().lower()


def _send_sms(phone, code):
    """Point d'intégration d'un vrai fournisseur SMS (à implémenter plus tard).

    Retourne True si le SMS a été envoyé. En mode simulé, ne fait rien.
    """
    if not SMS_ENABLED:
        return False
    # TODO: brancher Twilio / autre ici quand les identifiants seront fournis.
    return False


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
# Demande de code SMS (OTP)
# ------------------------------------------------------------
@auth_bp.post("/request-otp")
def request_otp():
    data = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    if not phone:
        return jsonify({"error": "Numéro de téléphone requis"}), 400

    code = f"{random.randint(0, 999999):06d}"
    otp = db.session.get(PhoneOtp, phone)
    if otp is None:
        otp = PhoneOtp(phone=phone)
        db.session.add(otp)
    otp.code = code
    otp.expires_at = _now() + timedelta(minutes=OTP_TTL_MINUTES)
    otp.attempts = 0
    db.session.commit()

    sent = _send_sms(phone, code)
    payload = {"sent": sent, "expiresIn": OTP_TTL_MINUTES * 60}
    # Mode simulé : on renvoie le code pour permettre les tests.
    if not sent:
        payload["devCode"] = code
    return jsonify(payload)


def _verify_otp(phone, code):
    """Vérifie un code OTP. Retourne (ok, message)."""
    otp = db.session.get(PhoneOtp, phone)
    if otp is None:
        return False, "Demandez d'abord un code de vérification"
    if otp.expires_at.replace(tzinfo=timezone.utc) < _now():
        return False, "Code expiré, demandez-en un nouveau"
    if otp.attempts >= 5:
        return False, "Trop de tentatives, demandez un nouveau code"
    if (code or "").strip() != otp.code:
        otp.attempts += 1
        db.session.commit()
        return False, "Code incorrect"
    return True, None


@auth_bp.post("/verify-otp")
def verify_otp():
    data = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    code = (data.get("code") or "").strip()
    ok, message = _verify_otp(phone, code)
    if not ok:
        return jsonify({"error": message}), 400
    return jsonify({"verified": True})


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

    # Vérification du code SMS (OTP).
    ok, message = _verify_otp(phone, otp_code)
    if not ok:
        return jsonify({"error": message}), 400

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

    # Le code OTP a servi : on le supprime.
    otp = db.session.get(PhoneOtp, phone)
    if otp is not None:
        db.session.delete(otp)

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
        user = User.query.filter_by(phone=phone).first()
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
