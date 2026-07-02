from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or len(password) < 4:
        return (
            jsonify(
                {"error": "Nom, e-mail et mot de passe (min. 4 caractères) requis"}
            ),
            400,
        )

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "Un compte existe déjà avec cet e-mail"}), 409

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "E-mail ou mot de passe incorrect"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    return jsonify(user.to_dict())


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
