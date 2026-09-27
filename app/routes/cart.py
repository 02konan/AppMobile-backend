from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import CartItem, Product


cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")


# ============================================================
# CONFIGURATION
# ============================================================

FREE_SHIPPING_THRESHOLD = 50.0
SHIPPING_COST = 4.99

# Empêche un client d'ajouter une quantité énorme
# en une seule requête.
MAX_CART_QUANTITY = 100

# Limites pour les variantes du produit.
MAX_OPTION_LENGTH = 100


# ============================================================
# OUTILS DE VALIDATION
# ============================================================

def _get_user_id():
    """
    Récupère l'identifiant de l'utilisateur depuis le JWT.

    Retourne:
        (user_id, None)
    ou:
        (None, response)
    """

    try:
        identity = get_jwt_identity()
        user_id = int(identity)

        if user_id <= 0:
            raise ValueError

        return user_id, None

    except (TypeError, ValueError):
        return None, (
            jsonify({
                "error": "Identité utilisateur invalide"
            }),
            401,
        )


def _get_json_body():
    """
    Vérifie que la requête contient un objet JSON valide.
    """

    if not request.is_json:
        return None, (
            jsonify({
                "error": "Content-Type doit être application/json"
            }),
            415,
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None, (
            jsonify({
                "error": "Le corps JSON doit être un objet"
            }),
            400,
        )

    return data, None


def _check_allowed_fields(data, allowed_fields):
    """
    Refuse les champs inconnus.
    """

    unexpected = set(data.keys()) - set(allowed_fields)

    if unexpected:
        return (
            jsonify({
                "error": "Champs non autorisés",
                "fields": sorted(unexpected),
            }),
            400,
        )

    return None


def _validate_positive_integer(
    value,
    field,
    minimum=1,
    maximum=None,
):
    """
    Valide un entier positif.

    Attention:
    bool est refusé car en Python bool est une sous-classe
    de int.
    """

    if isinstance(value, bool):
        return None, f"{field} doit être un nombre entier"

    # On accepte les entiers JSON.
    if isinstance(value, int):
        number = value

    # On accepte également une chaîne numérique simple.
    elif isinstance(value, str):
        value = value.strip()

        if not value:
            return None, f"{field} est requis"

        # Évite d'accepter "1.5", "1e10", etc.
        if not value.isdigit():
            return None, f"{field} doit être un nombre entier"

        try:
            number = int(value)
        except ValueError:
            return None, f"{field} invalide"

    else:
        return None, f"{field} doit être un nombre entier"

    if number < minimum:
        return None, f"{field} doit être >= {minimum}"

    if maximum is not None and number > maximum:
        return None, (
            f"{field} doit être <= {maximum}"
        )

    return number, None


def _validate_option(value, field):
    """
    Valide selectedColor / selectedSize.

    Les variantes sont optionnelles.
    """

    if value is None:
        return None, None

    if not isinstance(value, str):
        return None, (
            f"{field} doit être une chaîne de caractères"
        )

    value = value.strip()

    if len(value) > MAX_OPTION_LENGTH:
        return None, (
            f"{field} ne peut pas dépasser "
            f"{MAX_OPTION_LENGTH} caractères"
        )

    return value or None, None


# ============================================================
# CALCUL DU PANIER
# ============================================================

def _cart_summary(user_id):
    """
    Construit le résumé du panier de l'utilisateur.
    """

    items = (
        CartItem.query
        .filter_by(user_id=user_id)
        .all()
    )

    items_dicts = [
        item.to_dict()
        for item in items
    ]

    subtotal = round(
        sum(
            item["totalPrice"]
            for item in items_dicts
        ),
        2,
    )

    shipping_cost = (
        0.0
        if (
            subtotal == 0
            or subtotal >= FREE_SHIPPING_THRESHOLD
        )
        else SHIPPING_COST
    )

    return {
        "items": items_dicts,
        "itemCount": sum(
            item["quantity"]
            for item in items_dicts
        ),
        "subtotal": subtotal,
        "shippingCost": shipping_cost,
        "total": round(
            subtotal + shipping_cost,
            2,
        ),
    }


# ============================================================
# OBTENIR LE PANIER
# ============================================================

@cart_bp.get("")
@jwt_required()
def get_cart():

    user_id, error = _get_user_id()

    if error:
        return error

    return jsonify(
        _cart_summary(user_id)
    )


# ============================================================
# AJOUTER AU PANIER
# ============================================================

@cart_bp.post("")
@jwt_required()
def add_to_cart():

    # --------------------------------------------------------
    # Utilisateur
    # --------------------------------------------------------

    user_id, error = _get_user_id()

    if error:
        return error

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    data, error = _get_json_body()

    if error:
        return error

    # --------------------------------------------------------
    # Champs autorisés
    # --------------------------------------------------------

    allowed_fields = {
        "productId",
        "quantity",
        "selectedColor",
        "selectedSize",
    }

    error = _check_allowed_fields(
        data,
        allowed_fields,
    )

    if error:
        return error

    # --------------------------------------------------------
    # Product ID
    # --------------------------------------------------------

    product_id, error_message = _validate_positive_integer(
        data.get("productId"),
        "productId",
        minimum=1,
    )

    if error_message:
        return jsonify({
            "error": error_message
        }), 400

    # --------------------------------------------------------
    # Quantité
    # --------------------------------------------------------

    quantity, error_message = _validate_positive_integer(
        data.get("quantity", 1),
        "quantity",
        minimum=1,
        maximum=MAX_CART_QUANTITY,
    )

    if error_message:
        return jsonify({
            "error": error_message
        }), 400

    # --------------------------------------------------------
    # Couleur
    # --------------------------------------------------------

    color, error_message = _validate_option(
        data.get("selectedColor"),
        "selectedColor",
    )

    if error_message:
        return jsonify({
            "error": error_message
        }), 400

    # --------------------------------------------------------
    # Taille
    # --------------------------------------------------------

    size, error_message = _validate_option(
        data.get("selectedSize"),
        "selectedSize",
    )

    if error_message:
        return jsonify({
            "error": error_message
        }), 400

    # --------------------------------------------------------
    # Produit
    # --------------------------------------------------------

    product = db.session.get(
        Product,
        product_id,
    )

    if product is None:
        return jsonify({
            "error": "Produit introuvable"
        }), 404

    # --------------------------------------------------------
    # Recherche article existant
    # --------------------------------------------------------

    item = (
        CartItem.query
        .filter_by(
            user_id=user_id,
            product_id=product_id,
            selected_color=color,
            selected_size=size,
        )
        .first()
    )

    # --------------------------------------------------------
    # Mise à jour / création
    # --------------------------------------------------------

    if item:

        new_quantity = item.quantity + quantity

        if new_quantity > MAX_CART_QUANTITY:
            return jsonify({
                "error": (
                    f"La quantité maximale pour "
                    f"un article est de "
                    f"{MAX_CART_QUANTITY}"
                )
            }), 400

        item.quantity = new_quantity

    else:

        item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            selected_color=color,
            selected_size=size,
        )

        db.session.add(item)

    # --------------------------------------------------------
    # Sauvegarde
    # --------------------------------------------------------

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify({
            "error": (
                "Impossible de mettre à jour "
                "le panier"
            )
        }), 500

    return jsonify(
        _cart_summary(user_id)
    ), 201


# ============================================================
# MODIFIER UN ARTICLE DU PANIER
# ============================================================

@cart_bp.put("/<int:item_id>")
@jwt_required()
def update_cart_item(item_id):

    # --------------------------------------------------------
    # Validation item_id
    # --------------------------------------------------------

    if item_id <= 0:
        return jsonify({
            "error": "Identifiant d'article invalide"
        }), 400

    # --------------------------------------------------------
    # Utilisateur
    # --------------------------------------------------------

    user_id, error = _get_user_id()

    if error:
        return error

    # --------------------------------------------------------
    # Article appartenant à l'utilisateur
    # --------------------------------------------------------

    item = (
        CartItem.query
        .filter_by(
            id=item_id,
            user_id=user_id,
        )
        .first()
    )

    if item is None:
        return jsonify({
            "error": "Article introuvable"
        }), 404

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    data, error = _get_json_body()

    if error:
        return error

    # --------------------------------------------------------
    # Champs autorisés
    # --------------------------------------------------------

    allowed_fields = {
        "quantity",
    }

    error = _check_allowed_fields(
        data,
        allowed_fields,
    )

    if error:
        return error

    # --------------------------------------------------------
    # Quantité
    # --------------------------------------------------------

    quantity, error_message = _validate_positive_integer(
        data.get("quantity"),
        "quantity",
        minimum=1,
        maximum=MAX_CART_QUANTITY,
    )

    if error_message:
        return jsonify({
            "error": error_message
        }), 400

    # --------------------------------------------------------
    # Mise à jour
    # --------------------------------------------------------

    item.quantity = quantity

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify({
            "error": (
                "Impossible de mettre à jour "
                "le panier"
            )
        }), 500

    return jsonify(
        _cart_summary(user_id)
    )


# ============================================================
# SUPPRIMER UN ARTICLE
# ============================================================

@cart_bp.delete("/<int:item_id>")
@jwt_required()
def remove_cart_item(item_id):

    # --------------------------------------------------------
    # Validation item_id
    # --------------------------------------------------------

    if item_id <= 0:
        return jsonify({
            "error": "Identifiant d'article invalide"
        }), 400

    # --------------------------------------------------------
    # Utilisateur
    # --------------------------------------------------------

    user_id, error = _get_user_id()

    if error:
        return error

    # --------------------------------------------------------
    # Recherche article
    # --------------------------------------------------------

    item = (
        CartItem.query
        .filter_by(
            id=item_id,
            user_id=user_id,
        )
        .first()
    )

    # --------------------------------------------------------
    # Suppression
    # --------------------------------------------------------

    if item is not None:

        try:

            db.session.delete(item)
            db.session.commit()

        except Exception:

            db.session.rollback()

            return jsonify({
                "error": (
                    "Impossible de supprimer "
                    "l'article"
                )
            }), 500

    return jsonify(
        _cart_summary(user_id)
    )


# ============================================================
# VIDER LE PANIER
# ============================================================

@cart_bp.delete("")
@jwt_required()
def clear_cart():

    # --------------------------------------------------------
    # Utilisateur
    # --------------------------------------------------------

    user_id, error = _get_user_id()

    if error:
        return error

    # --------------------------------------------------------
    # Suppression
    # --------------------------------------------------------

    try:

        (
            CartItem.query
            .filter_by(user_id=user_id)
            .delete(
                synchronize_session=False
            )
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify({
            "error": (
                "Impossible de vider "
                "le panier"
            )
        }), 500

    return jsonify(
        _cart_summary(user_id)
    )