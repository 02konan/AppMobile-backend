"""Petits utilitaires d'authentification partagés par les blueprints."""

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from .extensions import db
from .models import User


def current_user():
    """Retourne l'utilisateur connecté (ou None) à partir du token JWT."""
    identity = get_jwt_identity()
    if identity is None:
        return None
    return db.session.get(User, int(identity))


def require_roles(*roles):
    """Décorateur : exige un token valide ET un rôle autorisé."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            user = current_user()
            if user is None:
                return jsonify({"error": "Utilisateur introuvable"}), 404
            if roles and user.role not in roles:
                return jsonify({"error": "Accès refusé"}), 403
            return view(*args, user=user, **kwargs)

        return wrapped

    return decorator
