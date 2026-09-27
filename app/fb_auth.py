"""Vérification des jetons d'identité Firebase (Firebase Phone Auth).

L'application envoie le SMS et vérifie le code via Firebase côté client, puis
transmet un `firebaseIdToken` au backend. Ici, on vérifie ce jeton avec le SDK
Firebase Admin pour obtenir le numéro de téléphone vérifié.

Configuration (variables d'environnement, l'une des deux) :
  - FIREBASE_CREDENTIALS_JSON : le contenu JSON de la clé de compte de service
  - FIREBASE_CREDENTIALS_FILE ou GOOGLE_APPLICATION_CREDENTIALS : chemin du fichier

Sans configuration, is_configured() renvoie False et verify_id_token() None.
"""

import json
import os

_app = None
_init_tried = False


def _init():
    """Initialise (une seule fois) l'app Firebase Admin, si configurée."""
    global _app, _init_tried
    if _app is not None or _init_tried:
        return _app
    _init_tried = True
    try:
        import firebase_admin
        from firebase_admin import credentials

        # Réutilise l'app par défaut si déjà initialisée ailleurs.
        try:
            _app = firebase_admin.get_app()
            return _app
        except ValueError:
            pass

        raw = os.environ.get("FIREBASE_CREDENTIALS_JSON")
        path = os.environ.get("FIREBASE_CREDENTIALS_FILE") or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        cred = None
        if raw:
            cred = credentials.Certificate(json.loads(raw))
        elif path and os.path.exists(path):
            cred = credentials.Certificate(path)

        if cred is not None:
            _app = firebase_admin.initialize_app(cred)
    except Exception:
        _app = None
    return _app


def is_configured():
    return _init() is not None


def verify_id_token(token):
    """Vérifie un jeton Firebase et renvoie ses claims (dont phone_number),
    ou None si non configuré / jeton invalide."""
    if _init() is None:
        return None
    try:
        from firebase_admin import auth as fb_auth

        return fb_auth.verify_id_token(token)
    except Exception:
        return None
