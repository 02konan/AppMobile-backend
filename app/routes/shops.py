from flask import Blueprint, jsonify, request

from ..auth_utils import require_roles
from ..extensions import db
from ..models import Category, Order, Product, ProductColor, ProductSize, Shop

shops_bp = Blueprint("shops", __name__, url_prefix="/api/shops")


def _next_product_id():
    rows = Product.query.with_entities(Product.id).all()
    numbers = [
        int(r.id[1:])
        for r in rows
        if r.id.startswith("p") and r.id[1:].isdigit()
    ]
    return f"p{(max(numbers) + 1) if numbers else 1}"


def _apply_variants(product, colors, sizes):
    ProductColor.query.filter_by(product_id=product.id).delete()
    ProductSize.query.filter_by(product_id=product.id).delete()
    for color in colors or []:
        color = str(color).strip()
        if color:
            db.session.add(ProductColor(product_id=product.id, color=color))
    for size in sizes or []:
        size = str(size).strip()
        if size:
            db.session.add(ProductSize(product_id=product.id, size=size))


# ------------------------------------------------------------
# Profil boutique
# ------------------------------------------------------------
@shops_bp.get("")
def list_shops():
    """Boutiques validées, visibles publiquement."""
    shops = (
        Shop.query.filter_by(status="validated").order_by(Shop.name).all()
    )
    return jsonify([s.to_dict() for s in shops])


@shops_bp.get("/me")
@require_roles("merchant")
def my_shop(user):
    if user.shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404
    return jsonify(user.shop.to_dict())


@shops_bp.put("/me")
@require_roles("merchant")
def update_my_shop(user):
    shop = user.shop
    if shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404

    data = request.get_json(silent=True) or {}
    for field, attr in (
        ("name", "name"),
        ("logoUrl", "logo_url"),
        ("coverUrl", "cover_url"),
        ("description", "description"),
        ("phone", "phone"),
        ("whatsapp", "whatsapp"),
        ("address", "address"),
        ("commune", "commune"),
        ("hours", "hours"),
        ("category", "category"),
    ):
        if field in data:
            value = data[field]
            setattr(shop, attr, value.strip() if isinstance(value, str) else value)

    if not shop.name:
        return jsonify({"error": "Le nom de la boutique est obligatoire"}), 400

    db.session.commit()
    return jsonify(shop.to_dict())


@shops_bp.get("/orders")
@require_roles("merchant")
def my_shop_orders(user):
    """Commandes reçues par la boutique du commerçant (récentes d'abord)."""
    if user.shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404
    query = Order.query.filter_by(shop_id=user.shop.id)
    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders])


@shops_bp.get("/<int:shop_id>")
def get_shop(shop_id):
    shop = db.session.get(Shop, shop_id)
    if shop is None:
        return jsonify({"error": "Boutique introuvable"}), 404
    return jsonify(shop.to_dict())


# ------------------------------------------------------------
# Produits du commerçant
# ------------------------------------------------------------
@shops_bp.get("/products")
@require_roles("merchant")
def list_my_products(user):
    if user.shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404
    products = (
        Product.query.filter_by(shop_id=user.shop.id)
        .order_by(Product.name)
        .all()
    )
    return jsonify([p.to_dict() for p in products])


@shops_bp.post("/products")
@require_roles("merchant")
def create_my_product(user):
    if user.shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    category_id = (data.get("categoryId") or "").strip()

    if not name or not category_id:
        return jsonify({"error": "Nom et catégorie obligatoires"}), 400
    if db.session.get(Category, category_id) is None:
        return jsonify({"error": "Catégorie invalide"}), 400

    try:
        price = float(data.get("price"))
        old_price = (
            float(data["oldPrice"])
            if data.get("oldPrice") not in (None, "")
            else None
        )
    except (TypeError, ValueError):
        return jsonify({"error": "Prix invalide"}), 400

    product = Product(
        id=_next_product_id(),
        shop_id=user.shop.id,
        category_id=category_id,
        name=name,
        description=(data.get("description") or "").strip(),
        price=price,
        old_price=old_price,
        image_url=(data.get("imageUrl") or "").strip(),
        stock=int(data.get("stock") or 0),
        is_featured=bool(data.get("isFeatured")),
        is_active=bool(data.get("isActive", True)),
    )
    db.session.add(product)
    db.session.flush()
    _apply_variants(product, data.get("colors"), data.get("sizes"))
    db.session.commit()
    return jsonify(product.to_dict()), 201


@shops_bp.put("/products/<product_id>")
@require_roles("merchant")
def update_my_product(user, product_id):
    if user.shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404

    product = db.session.get(Product, product_id)
    if product is None or product.shop_id != user.shop.id:
        return jsonify({"error": "Produit introuvable"}), 404

    data = request.get_json(silent=True) or {}
    if data.get("name"):
        product.name = data["name"].strip()
    if "description" in data:
        product.description = (data["description"] or "").strip()
    if "categoryId" in data and data["categoryId"]:
        if db.session.get(Category, data["categoryId"]) is None:
            return jsonify({"error": "Catégorie invalide"}), 400
        product.category_id = data["categoryId"]
    if "price" in data:
        try:
            product.price = float(data["price"])
        except (TypeError, ValueError):
            return jsonify({"error": "Prix invalide"}), 400
    if "oldPrice" in data:
        product.old_price = (
            float(data["oldPrice"]) if data["oldPrice"] not in (None, "") else None
        )
    if "imageUrl" in data:
        product.image_url = (data["imageUrl"] or "").strip()
    if "stock" in data:
        product.stock = int(data["stock"] or 0)
    if "isFeatured" in data:
        product.is_featured = bool(data["isFeatured"])
    if "isActive" in data:
        product.is_active = bool(data["isActive"])
    if "colors" in data or "sizes" in data:
        _apply_variants(product, data.get("colors"), data.get("sizes"))

    db.session.commit()
    return jsonify(product.to_dict())


@shops_bp.delete("/products/<product_id>")
@require_roles("merchant")
def delete_my_product(user, product_id):
    if user.shop is None:
        return jsonify({"error": "Aucune boutique pour ce compte"}), 404
    product = db.session.get(Product, product_id)
    if product is None or product.shop_id != user.shop.id:
        return jsonify({"error": "Produit introuvable"}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({"deleted": product_id})
