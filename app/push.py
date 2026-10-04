"""Notifications push via Firebase Cloud Messaging (FCM).

Best-effort : si Firebase n'est pas configuré (FIREBASE_SERVICE_ACCOUNT_JSON
absent) ou si l'envoi échoue, on n'interrompt jamais la requête en cours.
L'envoi réseau se fait dans un thread détaché pour ne pas ralentir l'API.
"""

import json
import os
import threading

import firebase_admin
from firebase_admin import credentials, messaging


def _admin_app():
    """Retourne l'app Firebase Admin, ou None si non configurée."""
    try:
        return firebase_admin.get_app()
    except ValueError:
        service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            return None
        try:
            service_account = json.loads(service_account_json)
            return firebase_admin.initialize_app(
                credentials.Certificate(service_account)
            )
        except Exception:
            return None


def _send(tokens, title, body, data):
    app = _admin_app()
    if app is None or not tokens:
        return
    payload = {k: str(v) for k, v in (data or {}).items()}
    # FCM limite un multicast à 500 jetons ; on découpe par lots.
    for i in range(0, len(tokens), 500):
        batch = tokens[i : i + 500]
        try:
            message = messaging.MulticastMessage(
                tokens=batch,
                notification=messaging.Notification(title=title, body=body),
                data=payload,
            )
            messaging.send_each_for_multicast(message, app=app)
        except Exception:
            # Envoi best-effort : on ignore les erreurs (jetons périmés, etc.)
            pass


def send_to_tokens(tokens, title, body, data=None):
    """Envoie une notification à une liste de jetons (en arrière-plan)."""
    tokens = [t for t in (tokens or []) if t]
    if not tokens:
        return
    threading.Thread(
        target=_send, args=(tokens, title, body, data), daemon=True
    ).start()


def notify_users(user_ids, title, body, data=None, exclude_user_id=None):
    """Notifie une liste d'utilisateurs (via leurs appareils enregistrés)."""
    from .models import DeviceToken

    ids = [uid for uid in set(user_ids or []) if uid != exclude_user_id]
    if not ids:
        return
    rows = DeviceToken.query.filter(DeviceToken.user_id.in_(ids)).all()
    send_to_tokens([r.token for r in rows], title, body, data)


def notify_all(title, body, data=None, exclude_user_id=None):
    """Notifie tous les appareils enregistrés (diffusion générale)."""
    from .models import DeviceToken

    query = DeviceToken.query
    if exclude_user_id is not None:
        query = query.filter(DeviceToken.user_id != exclude_user_id)
    rows = query.all()
    send_to_tokens([r.token for r in rows], title, body, data)
