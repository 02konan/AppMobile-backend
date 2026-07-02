from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Product

products_bp = Blueprint("products", __name__, url_prefix="/api/products")


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
