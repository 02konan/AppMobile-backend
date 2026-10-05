"""Intégration CinetPay (paiement mobile money + carte, Afrique de l'Ouest).

Couvre Orange Money, MTN MoMo, Moov Money, Wave et cartes via un seul
branchement. Utilisé pour le paiement de l'abonnement vendeur.

Configuration (variables d'environnement) :
  - CINETPAY_API_KEY    : clé API (tableau de bord CinetPay)
  - CINETPAY_SITE_ID    : identifiant du site
  - CINETPAY_SECRET_KEY : (optionnel) clé secrète pour vérifier le HMAC du
                          webhook. La confirmation se fait de toute façon par
                          un appel serveur-à-serveur /check (source de vérité).
  - CINETPAY_NOTIFY_URL : (optionnel) URL publique de notification serveur
  - CINETPAY_RETURN_URL : (optionnel) URL de retour après paiement

Tant que les clés ne sont pas définies, `is_configured()` renvoie False et le
code appelant retombe sur le comportement « paiement non configuré ».
"""

import os

import requests

_BASE_URL = "https://api-checkout.cinetpay.com/v2"
_TIMEOUT = 20


def _api_key():
    return os.environ.get("CINETPAY_API_KEY")


def _site_id():
    return os.environ.get("CINETPAY_SITE_ID")


def is_configured():
    return bool(_api_key() and _site_id())


def notify_url():
    return os.environ.get("CINETPAY_NOTIFY_URL")


def return_url():
    return os.environ.get("CINETPAY_RETURN_URL")


def init_payment(
    transaction_id,
    amount,
    description,
    customer_name=None,
    customer_phone=None,
):
    """Initialise un paiement et renvoie (payment_url, payment_token).

    Lève RuntimeError si CinetPay n'est pas configuré ou si l'init échoue.
    Le montant doit être un entier (FCFA), multiple de 5 exigé par CinetPay.
    """
    if not is_configured():
        raise RuntimeError("CinetPay non configuré")

    amount = int(round(amount))
    if amount % 5 != 0:
        amount = amount - (amount % 5)

    payload = {
        "apikey": _api_key(),
        "site_id": _site_id(),
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": "XOF",
        "description": description[:255],
        "channels": "ALL",
        "metadata": "divix-subscription",
    }
    if notify_url():
        payload["notify_url"] = notify_url()
    if return_url():
        payload["return_url"] = return_url()
    if customer_name:
        payload["customer_name"] = customer_name[:100]
    if customer_phone:
        payload["customer_phone_number"] = customer_phone

    resp = requests.post(
        f"{_BASE_URL}/payment", json=payload, timeout=_TIMEOUT
    )
    data = resp.json()
    if str(data.get("code")) != "201":
        raise RuntimeError(data.get("message") or "Échec d'initialisation")
    body = data.get("data") or {}
    return body.get("payment_url"), body.get("payment_token")


def check_payment(transaction_id):
    """Vérifie l'état d'une transaction (source de vérité).

    Renvoie un dict {status, amount, raw} où status ∈
    {'ACCEPTED', 'REFUSED', 'PENDING', 'UNKNOWN'}.
    """
    if not is_configured():
        return {"status": "UNKNOWN", "amount": None, "raw": None}

    payload = {
        "apikey": _api_key(),
        "site_id": _site_id(),
        "transaction_id": transaction_id,
    }
    try:
        resp = requests.post(
            f"{_BASE_URL}/payment/check", json=payload, timeout=_TIMEOUT
        )
        data = resp.json()
    except Exception:
        return {"status": "UNKNOWN", "amount": None, "raw": None}

    body = data.get("data") or {}
    code = str(data.get("code"))
    op_status = (body.get("status") or "").upper()

    if code == "00" or op_status == "ACCEPTED":
        status = "ACCEPTED"
    elif op_status in ("REFUSED", "CANCELED", "CANCELLED"):
        status = "REFUSED"
    elif op_status in ("PENDING", "WAITING_FOR_CUSTOMER", "WAITING"):
        status = "PENDING"
    else:
        # code 662 = en attente de paiement ; autres = non abouti.
        status = "PENDING" if code == "662" else "REFUSED"

    return {"status": status, "amount": body.get("amount"), "raw": data}
