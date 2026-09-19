from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Shop, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

VALID_ROLES = ("buyer", "merchant")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or "buyer").strip()
    email = (data.get("email") or "").strip().lower() or None

    if not name or not phone or len(password) < 4:
        return (
            jsonify(
                {
                    "error": "Nom, téléphone et mot de passe (min. 4 caractères) requis"
                }
            ),
            400,
        )

    if role not in VALID_ROLES:
        return jsonify({"error": "Type de compte invalide"}), 400

    if User.query.filter_by(phone=phone).first() is not None:
        return jsonify({"error": "Un compte existe déjà avec ce téléphone"}), 409

    if email and User.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "Un compte existe déjà avec cet e-mail"}), 409

    user = User(name=name, phone=phone, email=email, role=role)
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

    db.session.commit()
    return jsonify(user.to_dict())
