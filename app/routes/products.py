from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..auth_utils import current_user
from ..extensions import db
from ..features import require_feature
from ..models import Order, OrderItem, Product, Review

products_bp = Blueprint("products", __name__, url_prefix="/api/products")


def _recompute_rating(product):
    """Met à jour note moyenne + nombre d'avis du produit (dénormalisé)."""
    rows = Review.query.filter_by(product_id=product.id).all()
    count = len(rows)
    product.review_count = count
    product.rating = (
        round(sum(r.rating for r in rows) / count, 1) if count else 0
    )


def _has_purchased(user_id, product_id):
    """L'utilisateur a-t-il déjà commandé ce produit ?"""
    return (
        db.session.query(OrderItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id, OrderItem.product_id == product_id)
        .first()
        is not None
    )


@products_bp.get("")
def list_products():
    query = Product.query

    category_id = request.args.get("category")
    if category_id:
        query = query.filter_by(category_id=category_id)

    featured = request.args.get("featured")
    if featured is not None:
        want_featured = featured.lower() in ("1", "true", "yes")
        query = query.filter_by(is_featured=want_featured)

    search = request.args.get("q")
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Product.name.ilike(like), Product.description.ilike(like))
        )

    products = query.order_by(Product.name).all()
    return jsonify([p.to_dict() for p in products])


@products_bp.get("/<product_id>")
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify({"error": "Produit introuvable"}), 404
    return jsonify(product.to_dict())


# ------------------------------------------------------------
# Avis & notes (derrière le flag "reviews")
# ------------------------------------------------------------
@products_bp.get("/<product_id>/reviews")
def list_reviews(product_id):
    err = require_feature("reviews")
    if err:
        return err
    if db.session.get(Product, product_id) is None:
        return jsonify({"error": "Produit introuvable"}), 404
    reviews = (
        Review.query.filter_by(product_id=product_id)
        .order_by(Review.id.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in reviews])


@products_bp.post("/<product_id>/reviews")
@jwt_required()
def create_review(product_id):
    err = require_feature("reviews")
    if err:
        return err
    user = current_user()
    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify({"error": "Produit introuvable"}), 404

    data = request.get_json(silent=True) or {}
    try:
        rating = int(data.get("rating"))
    except (TypeError, ValueError):
        return jsonify({"error": "Note invalide"}), 400
    if rating < 1 or rating > 5:
        return jsonify({"error": "La note doit être entre 1 et 5"}), 400

    if not _has_purchased(user.id, product_id):
        return (
            jsonify(
                {"error": "Vous pouvez noter un produit après l'avoir commandé."}
            ),
            403,
        )

    comment = (data.get("comment") or "").strip()[:1000] or None

    # Un seul avis par utilisateur et par produit : on met à jour sinon on crée.
    review = Review.query.filter_by(
        product_id=product_id, user_id=user.id
    ).first()
    if review is None:
        review = Review(product_id=product_id, user_id=user.id)
        db.session.add(review)
    review.rating = rating
    review.comment = comment

    db.session.flush()
    _recompute_rating(product)
    db.session.commit()
    return jsonify(review.to_dict()), 201
