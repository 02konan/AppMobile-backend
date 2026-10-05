"""Configuration publique de l'app : feature flags.

- GET /api/config : lu par l'app au démarrage pour afficher/masquer des
  fonctionnalités (public).
- GET /api/config/flags : détail pour l'admin (clé + libellé + état).
- PUT /api/config/flags/<key> : activer/désactiver un flag (admin).
"""

from flask import Blueprint, jsonify, request

from ..auth_utils import require_roles
from ..features import DEFAULT_FLAGS, all_flags, detailed_flags, set_flag

config_bp = Blueprint("config", __name__, url_prefix="/api/config")


@config_bp.get("")
def get_config():
    """Flags effectifs, lus par l'application (aucune authentification)."""
    return jsonify({"flags": all_flags()})


@config_bp.get("/flags")
@require_roles("admin")
def list_flags(user):
    return jsonify(detailed_flags())


@config_bp.put("/flags/<key>")
@require_roles("admin")
def update_flag(user, key):
    if key not in DEFAULT_FLAGS:
        return jsonify({"error": "Flag inconnu"}), 404
    data = request.get_json(silent=True) or {}
    enabled = data.get("enabled")
    if not isinstance(enabled, bool):
        return jsonify({"error": "Champ 'enabled' (booléen) requis"}), 400
    set_flag(key, enabled)
    return jsonify({"key": key, "enabled": enabled})
