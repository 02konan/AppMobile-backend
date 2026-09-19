from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def _utcnow():
    return datetime.now(timezone.utc)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.String(30), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), nullable=False)

    products = db.relationship("Product", backref="category", lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "icon": self.icon}


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.String(30), primary_key=True)
    shop_id = db.Column(
        db.Integer, db.ForeignKey("shops.id"), nullable=True
    )
    category_id = db.Column(
        db.String(30), db.ForeignKey("categories.id"), nullable=False
    )
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    old_price = db.Column(db.Numeric(10, 2), nullable=True)
    image_url = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Numeric(2, 1), nullable=False, default=0)
    review_count = db.Column(db.Integer, nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=10)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    colors = db.relationship(
        "ProductColor", backref="product", lazy=True, cascade="all, delete-orphan"
    )
    sizes = db.relationship(
        "ProductSize", backref="product", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        price = float(self.price)
        old_price = float(self.old_price) if self.old_price is not None else None
        return {
            "id": self.id,
            "shopId": self.shop_id,
            "categoryId": self.category_id,
            "name": self.name,
            "description": self.description,
            "price": price,
            "oldPrice": old_price,
            "imageUrl": self.image_url,
            "rating": float(self.rating),
            "reviewCount": self.review_count,
            "stock": self.stock,
            "inStock": self.stock > 0,
            "isFeatured": bool(self.is_featured),
            "isActive": bool(self.is_active),
            "colors": [c.color for c in self.colors],
            "sizes": [s.size for s in self.sizes],
        }


class ProductColor(db.Model):
    __tablename__ = "product_colors"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.String(30), db.ForeignKey("products.id"), nullable=False
    )
    color = db.Column(db.String(50), nullable=False)


class ProductSize(db.Model):
    __tablename__ = "product_sizes"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.String(30), db.ForeignKey("products.id"), nullable=False
    )
    size = db.Column(db.String(20), nullable=False)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(
        db.Enum("buyer", "merchant", "admin", name="user_role"),
        nullable=False,
        default="buyer",
    )
    email = db.Column(db.String(150), nullable=True, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30), nullable=True, unique=True)
    address = db.Column(db.String(255), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    shop = db.relationship("Shop", backref="owner", uselist=False, lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "avatarUrl": self.avatar_url,
            "shopId": self.shop.id if self.shop else None,
        }


class Favorite(db.Model):
    __tablename__ = "favorites"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    product_id = db.Column(
        db.String(30), db.ForeignKey("products.id"), primary_key=True
    )
    created_at = db.Column(db.DateTime, default=_utcnow)

    product = db.relationship("Product", lazy=True)


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(
        db.String(30), db.ForeignKey("products.id"), nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False, default=1)
    selected_color = db.Column(db.String(50), nullable=True)
    selected_size = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    product = db.relationship("Product", lazy=True)

    def to_dict(self):
        product = self.product.to_dict()
        return {
            "id": self.id,
            "product": product,
            "quantity": self.quantity,
            "selectedColor": self.selected_color,
            "selectedSize": self.selected_size,
            "totalPrice": round(product["price"] * self.quantity, 2),
        }


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_cost = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_address = db.Column(db.String(255), nullable=False)
    payment_method = db.Column(
        db.Enum("card", "paypal", "cash", name="payment_method"),
        nullable=False,
        default="card",
    )
    status = db.Column(
        db.Enum("processing", "shipped", "delivered", name="order_status"),
        nullable=False,
        default="processing",
    )
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    items = db.relationship(
        "OrderItem", backref="order", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "orderNumber": self.order_number,
            "date": self.created_at.isoformat() if self.created_at else None,
            "subtotal": float(self.subtotal),
            "shippingCost": float(self.shipping_cost),
            "total": float(self.total),
            "shippingAddress": self.shipping_address,
            "paymentMethod": self.payment_method,
            "status": self.status,
            "items": [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(
        db.String(30), db.ForeignKey("products.id"), nullable=True
    )
    product_name = db.Column(db.String(150), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    selected_color = db.Column(db.String(50), nullable=True)
    selected_size = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "productId": self.product_id,
            "productName": self.product_name,
            "unitPrice": float(self.unit_price),
            "quantity": self.quantity,
            "selectedColor": self.selected_color,
            "selectedSize": self.selected_size,
            "totalPrice": round(float(self.unit_price) * self.quantity, 2),
        }


# ============================================================
# DIVIX LIVE — boutiques & lives
# ============================================================


class Shop(db.Model):
    __tablename__ = "shops"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True
    )
    name = db.Column(db.String(150), nullable=False)
    logo_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    whatsapp = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    commune = db.Column(db.String(100), nullable=True)
    hours = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    status = db.Column(
        db.Enum("pending", "validated", "suspended", name="shop_status"),
        nullable=False,
        default="pending",
    )
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    products = db.relationship("Product", backref="shop", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "name": self.name,
            "logoUrl": self.logo_url,
            "description": self.description,
            "phone": self.phone,
            "whatsapp": self.whatsapp,
            "address": self.address,
            "commune": self.commune,
            "hours": self.hours,
            "category": self.category,
            "status": self.status,
        }


# Produits sélectionnés pour un live (association many-to-many + position)
live_products = db.Table(
    "live_products",
    db.Column(
        "live_id", db.Integer, db.ForeignKey("lives.id"), primary_key=True
    ),
    db.Column(
        "product_id",
        db.String(30),
        db.ForeignKey("products.id"),
        primary_key=True,
    ),
    db.Column("position", db.Integer, nullable=False, default=0),
)


class Live(db.Model):
    __tablename__ = "lives"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.Enum("scheduled", "live", "ended", name="live_status"),
        nullable=False,
        default="scheduled",
    )
    current_product_id = db.Column(
        db.String(30), db.ForeignKey("products.id"), nullable=True
    )
    viewer_count = db.Column(db.Integer, nullable=False, default=0)
    playback_url = db.Column(db.String(500), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    shop = db.relationship("Shop", lazy=True)
    products = db.relationship(
        "Product",
        secondary=live_products,
        order_by=live_products.c.position,
        lazy=True,
    )
    current_product = db.relationship(
        "Product", foreign_keys=[current_product_id], lazy=True
    )

    def to_dict(self, with_products=False):
        data = {
            "id": self.id,
            "shopId": self.shop_id,
            "shopName": self.shop.name if self.shop else None,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "scheduledAt": self.scheduled_at.isoformat()
            if self.scheduled_at
            else None,
            "status": self.status,
            "currentProductId": self.current_product_id,
            "currentProduct": self.current_product.to_dict()
            if self.current_product
            else None,
            "viewerCount": self.viewer_count,
            "playbackUrl": self.playback_url,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "endedAt": self.ended_at.isoformat() if self.ended_at else None,
            "productCount": len(self.products),
        }
        if with_products:
            data["products"] = [p.to_dict() for p in self.products]
        return data
