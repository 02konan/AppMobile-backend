"""Abonnement vendeur DIVIX.

Structure prête pour un paiement mobile money (branchement fournisseur plus
tard). Pour l'instant : consultation du statut, création d'une intention de
paiement (pending), et activation possible par l'administration.

AUCUNE restriction n'est appliquée ailleurs : un vendeur non abonné continue
d'utiliser toutes les fonctions comme avant. Le blocage pourra être activé
plus tard à partir de shop.subscription_active.
"""

from datetime import timedelta

from flask import Blueprint, jsonify, request

from ..auth_utils import require_roles
from ..extensions import db
from ..models import SubscriptionPayment, _utcnow

subscription_bp = Blueprint(
    "subscription", __name__, url_prefix="/api/subscription"
)

# Offres d'abonnement (montants en FCFA).
PLANS = {
    "monthly": {"label": "Mensuel", "amount": 5000, "days": 30},
    "quarterly": {"label": "Trimestriel", "amount": 13000, "days": 90},
    "yearly": {"label": "Annuel", "amount": 45000, "days": 365},
}


def _plans_payload():
    return [
        {"id": pid, "label": p["label"], "amount": p["amount"], "days": p["days"]}
        for pid, p in PLANS.items()
    ]


def activate_subscription(shop, plan_id, days):
    """Prolonge l'abonnement d'une boutique (depuis la date d'expiration
    restante si elle est dans le futur, sinon depuis maintenant)."""
    now = _utcnow()
    current = shop.subscription_expires_at
    if current is not None and current.tzinfo is None:
        from datetime import timezone

        current = current.replace(tzinfo=timezone.utc)
    base = current if (current and current > now) else now
    shop.subscription_expires_at = base + timedelta(days=days)
    shop.subscription_plan = plan_id


@subscription_bp.get("/me")
@require_roles("merchant")
def my_subscription(user):
    if user.shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404
    shop = user.shop
    return jsonify(
        {
            "plan": shop.subscription_plan,
            "expiresAt": shop.subscription_expires_at.isoformat()
            if shop.subscription_expires_at
            else None,
            "active": shop.subscription_active,
            "plans": _plans_payload(),
        }
    )


@subscription_bp.post("/subscribe")
@require_roles("merchant")
def subscribe(user):
    """Crée une intention de paiement d'abonnement.

    Tant qu'aucun fournisseur mobile money n'est branché, le paiement reste
    « en attente » : un administrateur peut l'activer manuellement. Quand le
    fournisseur sera configuré, cette route initialisera la transaction et
    renverra l'URL/le jeton de paiement.
    """
    if user.shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404

    data = request.get_json(silent=True) or {}
    plan_id = (data.get("plan") or "monthly").strip()
    plan = PLANS.get(plan_id)
    if plan is None:
        return jsonify({"error": "Offre d'abonnement invalide"}), 400

    payment = SubscriptionPayment(
        shop_id=user.shop.id,
        plan=plan_id,
        amount=plan["amount"],
        days=plan["days"],
        provider=None,
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    return (
        jsonify(
            {
                "payment": payment.to_dict(),
                "paymentConfigured": False,
                "message": (
                    "Paiement en ligne bientôt disponible. Votre demande "
                    "d'abonnement a été enregistrée ; un administrateur peut "
                    "l'activer."
                ),
            }
        ),
        201,
    )
