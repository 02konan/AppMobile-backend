"""Génération des jetons de salle Agora (streaming vidéo temps réel).

Flask ne transporte pas la vidéo : il se contente de délivrer, pour chaque
participant, un jeton court signé avec le certificat Agora. Le commerçant
publie (broadcaster) et les acheteurs s'abonnent (viewer) via le SDK Agora.
"""

import time

from flask import current_app

try:  # dépendance optionnelle : l'API reste utilisable sans streaming
    from agora_token_builder import RtcTokenBuilder
except Exception:  # pragma: no cover
    RtcTokenBuilder = None

# Rôles RTC Agora
ROLE_PUBLISHER = 1
ROLE_SUBSCRIBER = 2


def is_configured():
    """True si l'App ID, le certificat et la lib sont disponibles."""
    return bool(
        current_app.config.get("AGORA_APP_ID")
        and current_app.config.get("AGORA_APP_CERTIFICATE")
        and RtcTokenBuilder is not None
    )


def build_rtc_token(channel, uid, publisher=False):
    """Construit un jeton RTC pour une salle (channel) et un uid donnés."""
    app_id = current_app.config["AGORA_APP_ID"]
    certificate = current_app.config["AGORA_APP_CERTIFICATE"]
    ttl = current_app.config.get("AGORA_TOKEN_TTL", 3600)
    role = ROLE_PUBLISHER if publisher else ROLE_SUBSCRIBER
    expire_at = int(time.time()) + ttl
    token = RtcTokenBuilder.buildTokenWithUid(
        app_id, certificate, channel, uid, role, expire_at
    )
    return token, ttl


def channel_for_live(live_id):
    """Nom de salle déterministe pour un live."""
    return f"live_{live_id}"
