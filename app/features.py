"""Feature flags DIVIX.

Permet de déployer du code « éteint » et de l'activer au fur et à mesure,
sans nouvelle version de l'app. Les valeurs par défaut vivent ici ; seules
les surcharges sont stockées en base (table feature_flags), modifiables
depuis l'admin.

Un cache mémoire (TTL court) évite de taper la base à chaque requête, ce qui
est important quand beaucoup d'utilisateurs consultent une fonctionnalité
protégée.
"""

import time

from flask import jsonify

# clé -> (activé par défaut, libellé lisible pour l'admin)
DEFAULT_FLAGS = {
    # Fonctionnalités gourmandes en ressources serveur.
    "lives": (True, "Lives (diffusion en direct — Agora)"),
    "reels": (True, "ReelShops (vidéos courtes — Cloudinary)"),
    "notifyLiveStart": (True, "Notification au démarrage d'un live (diffusion)"),
    "notifyNewReel": (True, "Notification nouveau ReelShop (diffusion)"),
    # Fonctionnalités à venir (livrées éteintes).
    "mobileMoney": (False, "Paiement mobile money"),
    "reviews": (False, "Avis & notes produits"),
}

_CACHE_TTL = 30  # secondes
_cache = {}
_cache_at = 0.0


def _refresh():
    global _cache, _cache_at
    from .models import FeatureFlag

    rows = FeatureFlag.query.all()
    _cache = {r.key: r.enabled for r in rows}
    _cache_at = time.time()


def _overrides():
    global _cache_at
    if time.time() - _cache_at > _CACHE_TTL:
        try:
            _refresh()
        except Exception:
            # En cas de souci base, on garde le cache précédent (ou vide =>
            # valeurs par défaut), sans jamais casser la requête.
            _cache_at = time.time()
    return _cache


def is_enabled(key):
    """La fonctionnalité est-elle active ? (surcharge base sinon défaut)."""
    overrides = _overrides()
    if key in overrides:
        return overrides[key]
    default = DEFAULT_FLAGS.get(key)
    return default[0] if default else False


def all_flags():
    """État effectif de tous les flags connus (défauts + surcharges)."""
    overrides = _overrides()
    result = {k: overrides.get(k, default) for k, (default, _) in DEFAULT_FLAGS.items()}
    for key, value in overrides.items():
        result.setdefault(key, value)
    return result


def detailed_flags():
    """Liste pour l'admin : clé, libellé, état effectif."""
    overrides = _overrides()
    out = []
    for key, (default, label) in DEFAULT_FLAGS.items():
        out.append(
            {"key": key, "label": label, "enabled": overrides.get(key, default)}
        )
    return out


def set_flag(key, enabled):
    from .extensions import db
    from .models import FeatureFlag

    row = FeatureFlag.query.filter_by(key=key).first()
    if row is None:
        row = FeatureFlag(key=key, enabled=bool(enabled))
        db.session.add(row)
    else:
        row.enabled = bool(enabled)
    db.session.commit()
    _refresh()
    return row


def require_feature(key):
    """Renvoie une réponse 503 si la fonctionnalité est désactivée, sinon None.

    À utiliser au début d'une route :
        err = require_feature("lives")
        if err: return err
    """
    if is_enabled(key):
        return None
    return (
        jsonify(
            {
                "error": "Cette fonctionnalité est momentanément indisponible.",
                "feature": key,
            }
        ),
        503,
    )
