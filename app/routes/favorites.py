from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Favorite, Product

favorites_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")


@favorites_bp.get("")
@jwt_required()
def list_favorites():
    user_id = int(get_jwt_identity())
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    return jsonify([f.product.to_dict() for f in favorites])


@favorites_bp.post("")
@jwt_required()
def add_favorite():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    product_id = data.get("productId")

    if not product_id:
        return jsonify({"error": "productId requis"}), 400
    if db.session.get(Product, product_id) is None:
        return jsonify({"error": "Produit introuvable"}), 404

    existing = Favorite.query.filter_by(
        user_id=user_id, product_id=product_id
    ).first()
    if existing is None:
        db.session.add(Favorite(user_id=user_id, product_id=product_id))
        db.session.commit()

    return jsonify({"success": True}), 201


@favorites_bp.delete("/<product_id>")
@jwt_required()
def remove_favorite(product_id):
    user_id = int(get_jwt_identity())
    favorite = Favorite.query.filter_by(
        user_id=user_id, product_id=product_id
    ).first()
    if favorite is not None:
        db.session.delete(favorite)
        db.session.commit()

    return jsonify({"success": True})
