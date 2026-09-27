import json
import os
import re

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from marshmallow import ValidationError

from .. import fb_auth
from ..extensions import db
from ..models import Shop, User
from ..schemas import (
    LoginSchema,
    RegisterSchema,
    UpdateProfileSchema,
    UsernameQuerySchema,
)


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)


VALID_ROLES = (
    "buyer",
    "merchant",
    "driver",
)

USERNAME_RE = re.compile(
    r"^[a-z0-9_]{3,30}$"
)


# ============================================================
# SCHÉMAS
# ============================================================

register_schema = RegisterSchema()
login_schema = LoginSchema()
update_profile_schema = UpdateProfileSchema()
username_query_schema = UsernameQuerySchema()


# ============================================================
# FIREBASE
# ============================================================

def _firebase_admin_app():
    """
    Retourne l'application Firebase Admin.

    Si elle n'existe pas encore, elle est initialisée
    à partir de FIREBASE_SERVICE_ACCOUNT_JSON.
    """

    try:
        return firebase_admin.get_app()

    except ValueError:

        service_account_json = os.environ.get(
            "FIREBASE_SERVICE_ACCOUNT_JSON"
        )

        if not service_account_json:
            raise RuntimeError(
                "Firebase Admin n'est pas configuré"
            )

        try:
            service_account = json.loads(
                service_account_json
            )

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON est invalide"
            ) from exc

        return firebase_admin.initialize_app(
            credentials.Certificate(
                service_account
            )
        )


# ============================================================
# OUTILS
# ============================================================

def _normalize_username(value):
    """
    Normalise un nom d'utilisateur.
    """

    if value is None:
        return None

    if not isinstance(value, str):
        return None

    return value.strip().lower()


def _get_json_body(schema):
    """
    Vérifie le Content-Type puis valide le JSON
    avec le schéma Marshmallow fourni.
    """

    if not request.is_json:
        return None, (
            jsonify({
                "error": (
                    "Content-Type doit être "
                    "application/json"
                )
            }),
            415,
        )

    data = request.get_json(silent=True)

<<<<<<< Updated upstream
    if not isinstance(data, dict):
        return None, (
            jsonify({
                "error": (
                    "Le corps JSON doit être "
                    "un objet"
                )
            }),
=======
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
    firebase_id_token = (data.get("firebaseIdToken") or "").strip()

    if not name or not phone or len(password) < 8:
        return (
            jsonify(
                {
                    "error": "Nom, téléphone et mot de passe (min. 8 caractères) requis"
                }
            ),
>>>>>>> Stashed changes
            400,
        )

    try:
        validated_data = schema.load(data)

    except ValidationError as exc:
        return None, (
            jsonify({
                "error": "Données invalides",
                "details": exc.messages,
            }),
            400,
        )

<<<<<<< Updated upstream
    return validated_data, None
=======
    # Vérification du numéro de téléphone.
    # Mode fournisseur (Firebase Phone Auth) : l'app envoie un jeton Firebase
    # que l'on vérifie côté serveur. Repli sur le code OTP interne (mode simulé
    # / tests) uniquement si aucun jeton n'est fourni.
    if firebase_id_token:
        claims = fb_auth.verify_id_token(firebase_id_token)
        if claims is None:
            if not fb_auth.is_configured():
                return (
                    jsonify(
                        {
                            "error": "Vérification du téléphone non configurée sur "
                            "le serveur (Firebase)."
                        }
                    ),
                    503,
                )
            return (
                jsonify({"error": "Vérification du numéro échouée. Réessayez."}),
                400,
            )
        # Le numéro vérifié par Firebase fait foi.
        verified_phone = (claims.get("phone_number") or "").strip()
        if verified_phone:
            phone = verified_phone
    else:
        ok, message = _verify_otp(phone, otp_code)
        if not ok:
            return jsonify({"error": message}), 400
>>>>>>> Stashed changes


def _get_current_user():
    """
    Récupère l'utilisateur correspondant au JWT.
    """

    try:
        user_id = int(get_jwt_identity())

    except (TypeError, ValueError):
        return None

    if user_id <= 0:
        return None

    return db.session.get(
        User,
        user_id,
    )


# ============================================================
# DISPONIBILITÉ DU NOM D'UTILISATEUR
# ============================================================

@auth_bp.get("/check-username")
def check_username():

    if not request.args:
        return jsonify({
            "available": False,
            "reason": "Nom d'utilisateur requis",
        }), 400

    try:
        data = username_query_schema.load(
            request.args.to_dict()
        )

    except ValidationError as exc:
        return jsonify({
            "available": False,
            "reason": exc.messages,
        }), 400

    username = _normalize_username(
        data["username"]
    )

    if not USERNAME_RE.match(username):
        return jsonify({
            "available": False,
            "reason": (
                "3 à 30 caractères : "
                "lettres, chiffres, _"
            ),
        })

    taken = (
        User.query
        .filter_by(username=username)
        .first()
        is not None
    )

    return jsonify({
        "available": not taken,
        "username": username,
    })


# ============================================================
# INSCRIPTION
# ============================================================

@auth_bp.post("/register")
def register():

    data, error = _get_json_body(
        register_schema
    )

    if error:
        return error

    # --------------------------------------------------------
    # Normalisation
    # --------------------------------------------------------

    name = data["name"].strip()

    phone = data["phone"].strip()

    password = data["password"]

    role = data.get(
        "role",
        "buyer",
    )

    email = data.get("email")

    if email:
        email = email.strip().lower()

    firebase_id_token = (
        data["firebaseIdToken"].strip()
    )

    username = _normalize_username(
        data.get("username")
    )

    country = data.get("country")

    if country:
        country = country.strip()

    city = data.get("city")

    if city:
        city = city.strip()

    # --------------------------------------------------------
    # Vérification du nom d'utilisateur
    # --------------------------------------------------------

    if username is not None:

        if not USERNAME_RE.match(username):
            return jsonify({
                "error": (
                    "Nom d'utilisateur invalide"
                )
            }), 400

        existing_username = (
            User.query
            .filter_by(username=username)
            .first()
        )

        if existing_username is not None:
            return jsonify({
                "error": (
                    "Ce nom d'utilisateur "
                    "est déjà pris"
                )
            }), 409

    # --------------------------------------------------------
    # Firebase
    # --------------------------------------------------------

    try:

        firebase_user = (
            firebase_auth.verify_id_token(
                firebase_id_token,
                app=_firebase_admin_app(),
            )
        )

    except RuntimeError:

        return jsonify({
            "error": (
                "La vérification Firebase "
                "n'est pas configurée"
            )
        }), 503

    except Exception:

        return jsonify({
            "error": (
                "Jeton Firebase invalide "
                "ou expiré"
            )
        }), 401

    # --------------------------------------------------------
    # Vérification téléphone Firebase
    # --------------------------------------------------------

    firebase_phone = (
        firebase_user.get("phone_number")
    )

    if firebase_phone != phone:
        return jsonify({
            "error": (
                "Le numéro vérifié "
                "ne correspond pas"
            )
        }), 403

    # --------------------------------------------------------
    # Téléphone déjà utilisé
    # --------------------------------------------------------

    existing_phone = (
        User.query
        .filter_by(phone=phone)
        .first()
    )

    if existing_phone is not None:
        return jsonify({
            "error": (
                "Un compte existe déjà "
                "avec ce téléphone"
            )
        }), 409

    # --------------------------------------------------------
    # E-mail déjà utilisé
    # --------------------------------------------------------

    if email:

        existing_email = (
            User.query
            .filter_by(email=email)
            .first()
        )

        if existing_email is not None:
            return jsonify({
                "error": (
                    "Un compte existe déjà "
                    "avec cet e-mail"
                )
            }), 409

    # --------------------------------------------------------
    # Création utilisateur
    # --------------------------------------------------------

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

    try:

        db.session.flush()

        # ----------------------------------------------------
        # Boutique marchand
        # ----------------------------------------------------

        if role == "merchant":

            shop_name = (
                data.get("shopName") or ""
            ).strip()

            if not shop_name:
                shop_name = (
                    f"Boutique de {name}"
                )

            shop = Shop(
                user_id=user.id,
                name=shop_name,
                whatsapp=phone,
                phone=phone,
            )

            db.session.add(shop)

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify({
            "error": (
                "Impossible de créer "
                "le compte"
            )
        }), 500

    # --------------------------------------------------------
    # Token
    # --------------------------------------------------------

    token = create_access_token(
        identity=str(user.id)
    )

    payload = {
        "token": token,
        "user": user.to_dict(),
    }

    if user.shop is not None:
        payload["shop"] = (
            user.shop.to_dict()
        )

    return jsonify(payload), 201


# ============================================================
# CONNEXION
# ============================================================

@auth_bp.post("/login")
def login():

    data, error = _get_json_body(
        login_schema
    )

    if error:
        return error

    phone = (
        data.get("phone") or ""
    ).strip()

    email = (
        data.get("email") or ""
    ).strip().lower()

    password = data["password"]

    user = None

    # --------------------------------------------------------
    # Connexion téléphone
    # --------------------------------------------------------

    if phone:

        digits = re.sub(
            r"\D",
            "",
            phone,
        )

        candidates = [
            phone,
            digits,
        ]

        if not phone.startswith("+"):

            candidates.append(
                f"+225{digits}"
            )

        for candidate in dict.fromkeys(
            candidates
        ):

            user = (
                User.query
                .filter_by(phone=candidate)
                .first()
            )

            if user is not None:
                break

    # --------------------------------------------------------
    # Connexion e-mail
    # --------------------------------------------------------

    if user is None and email:

        user = (
            User.query
            .filter_by(email=email)
            .first()
        )

    # --------------------------------------------------------
    # Vérification mot de passe
    # --------------------------------------------------------

    if (
        user is None
        or not user.check_password(password)
    ):
        return jsonify({
            "error": (
                "Téléphone ou mot de passe "
                "incorrect"
            )
        }), 401

    # --------------------------------------------------------
    # Token
    # --------------------------------------------------------

    token = create_access_token(
        identity=str(user.id)
    )

    payload = {
        "token": token,
        "user": user.to_dict(),
    }

    if user.shop is not None:
        payload["shop"] = (
            user.shop.to_dict()
        )

    return jsonify(payload)


# ============================================================
# PROFIL COURANT
# ============================================================

@auth_bp.get("/me")
@jwt_required()
def me():

    user = _get_current_user()

    if user is None:
        return jsonify({
            "error": "Utilisateur introuvable"
        }), 404

    payload = user.to_dict()

    if user.shop is not None:
        payload["shop"] = (
            user.shop.to_dict()
        )

    return jsonify(payload)


# ============================================================
# MODIFIER LE PROFIL
# ============================================================

@auth_bp.put("/me")
@jwt_required()
def update_me():

    user = _get_current_user()

    if user is None:
        return jsonify({
            "error": "Utilisateur introuvable"
        }), 404

    data, error = _get_json_body(
        update_profile_schema
    )

    if error:
        return error

    # --------------------------------------------------------
    # Nom
    # --------------------------------------------------------

    if "name" in data:
        user.name = data["name"].strip()

    # --------------------------------------------------------
    # Adresse
    # --------------------------------------------------------

    if "address" in data:
        user.address = data["address"]

    # --------------------------------------------------------
    # Ville
    # --------------------------------------------------------

    if "city" in data:
        user.city = (
            data["city"].strip()
            if data["city"]
            else None
        )

    # --------------------------------------------------------
    # Pays
    # --------------------------------------------------------

    if "country" in data:
        user.country = (
            data["country"].strip()
            if data["country"]
            else None
        )

    # --------------------------------------------------------
    # Sauvegarde
    # --------------------------------------------------------

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify({
            "error": (
                "Impossible de modifier "
                "le profil"
            )
        }), 500

    return jsonify(
        user.to_dict()
    )
