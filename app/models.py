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
    username = db.Column(db.String(50), nullable=True, unique=True)
    role = db.Column(
        db.Enum("buyer", "merchant", "admin", "driver", name="user_role"),
        nullable=False,
        default="buyer",
    )
    email = db.Column(db.String(150), nullable=True, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30), nullable=True, unique=True)
    phone_verified = db.Column(db.Boolean, nullable=False, default=False)
    country = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(100), nullable=True)
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
            "username": self.username,
            "role": self.role,
            "email": self.email,
            "phone": self.phone,
            "phoneVerified": bool(self.phone_verified),
            "country": self.country,
            "city": self.city,
            "address": self.address,
            "avatarUrl": self.avatar_url,
            "shopId": self.shop.id if self.shop else None,
        }


class PhoneOtp(db.Model):
    """Code de vérification SMS (OTP) associé à un numéro de téléphone.

    Un seul code actif par numéro (remplacé à chaque demande). En mode
    simulé (SMS non configuré), le code n'est pas envoyé mais renvoyé à
    l'app pour permettre les tests.
    """

    __tablename__ = "phone_otps"

    phone = db.Column(db.String(30), primary_key=True)
    code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=_utcnow)


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
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=True)
    live_id = db.Column(db.Integer, db.ForeignKey("lives.id"), nullable=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_cost = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_address = db.Column(db.String(255), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=True)
    payment_method = db.Column(
        db.Enum("card", "paypal", "cash", "whatsapp", name="payment_method"),
        nullable=False,
        default="whatsapp",
    )
    status = db.Column(
        db.Enum(
            "pending",
            "confirmed",
            "preparing",
            "ready",
            "picked_up",
            "delivering",
            "delivered",
            "refused",
            "cancelled",
            name="order_status",
        ),
        nullable=False,
        default="pending",
    )
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    items = db.relationship(
        "OrderItem", backref="order", lazy=True, cascade="all, delete-orphan"
    )
    user = db.relationship("User", lazy=True)
    shop = db.relationship("Shop", lazy=True)
    delivery = db.relationship(
        "Delivery",
        backref="order",
        uselist=False,
        lazy=True,
        cascade="all, delete-orphan",
    )

    # Libellés français des statuts (workflow DIVIX)
    STATUS_LABELS = {
        "pending": "En attente",
        "confirmed": "Confirmée",
        "preparing": "En préparation",
        "ready": "Prête",
        "picked_up": "Récupérée",
        "delivering": "En livraison",
        "delivered": "Livrée",
        "refused": "Refusée",
        "cancelled": "Annulée",
    }

    def to_dict(self):
        return {
            "id": self.id,
            "orderNumber": self.order_number,
            "userId": self.user_id,
            "shopId": self.shop_id,
            "liveId": self.live_id,
            "customerName": self.user.name if self.user else None,
            "date": self.created_at.isoformat() if self.created_at else None,
            "subtotal": float(self.subtotal),
            "shippingCost": float(self.shipping_cost),
            "total": float(self.total),
            "shippingAddress": self.shipping_address,
            "customerPhone": self.customer_phone,
            "paymentMethod": self.payment_method,
            "status": self.status,
            "statusLabel": self.STATUS_LABELS.get(self.status, self.status),
            "delivery": self.delivery.to_dict() if self.delivery else None,
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
    cover_url = db.Column(db.String(500), nullable=True)
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
    # Abonnement vendeur : la boutique est "abonnée" tant que
    # subscription_expires_at est dans le futur. (Aucune restriction appliquée
    # pour l'instant — le champ sert de base au futur blocage.)
    subscription_plan = db.Column(db.String(30), nullable=True)
    subscription_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    products = db.relationship("Product", backref="shop", lazy=True)

    @property
    def subscription_active(self):
        exp = self.subscription_expires_at
        if exp is None:
            return False
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp > _utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "name": self.name,
            "logoUrl": self.logo_url,
            "coverUrl": self.cover_url,
            "description": self.description,
            "phone": self.phone,
            "whatsapp": self.whatsapp,
            "address": self.address,
            "commune": self.commune,
            "hours": self.hours,
            "category": self.category,
            "status": self.status,
            "subscription": {
                "plan": self.subscription_plan,
                "expiresAt": self.subscription_expires_at.isoformat()
                if self.subscription_expires_at
                else None,
                "active": self.subscription_active,
            },
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
    cover_url = db.Column(db.String(500), nullable=True)
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

    messages = db.relationship(
        "LiveMessage", backref="live", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self, with_products=False):
        data = {
            "id": self.id,
            "shopId": self.shop_id,
            "shopName": self.shop.name if self.shop else None,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "coverUrl": self.cover_url,
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


class LiveViewer(db.Model):
    """Présence d'un spectateur sur un live (système de « heartbeat »).

    Chaque spectateur (connecté ou anonyme, identifié par une clé stable)
    signale régulièrement sa présence. Le nombre de vues d'un live = nombre
    de spectateurs vus dans une fenêtre récente (voir ACTIVE_WINDOW_SECONDS).
    Les lignes périmées sont purgées à chaque battement.
    """

    __tablename__ = "live_viewers"

    # Un spectateur est « actif » s'il a été vu dans les 25 dernières secondes.
    ACTIVE_WINDOW_SECONDS = 25

    id = db.Column(db.Integer, primary_key=True)
    live_id = db.Column(db.Integer, db.ForeignKey("lives.id"), nullable=False)
    viewer_key = db.Column(db.String(80), nullable=False)
    last_seen = db.Column(db.DateTime, default=_utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("live_id", "viewer_key", name="uq_live_viewer"),
    )


class LiveMessage(db.Model):
    __tablename__ = "live_messages"

    id = db.Column(db.Integer, primary_key=True)
    live_id = db.Column(db.Integer, db.ForeignKey("lives.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user_name = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "liveId": self.live_id,
            "userId": self.user_id,
            "userName": self.user_name,
            "message": self.message,
            "date": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================
# DIVIX — ReelShops (vidéos courtes shoppables, façon TikTok)
# ============================================================

# Produits associés à un reel (comme pour un live).
reel_products = db.Table(
    "reel_products",
    db.Column(
        "reel_id", db.Integer, db.ForeignKey("reels.id"), primary_key=True
    ),
    db.Column(
        "product_id",
        db.String(30),
        db.ForeignKey("products.id"),
        primary_key=True,
    ),
    db.Column("position", db.Integer, nullable=False, default=0),
)


class Reel(db.Model):
    """Vidéo courte (≤ 30 s) publiée par une boutique, avec des produits
    présentés en dessous (bouton « Acheter »). Vidéo hébergée sur Cloudinary.
    """

    __tablename__ = "reels"

    # Durée maximale autorisée pour une vidéo de reel (secondes).
    MAX_DURATION_SECONDS = 30

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    caption = db.Column(db.String(300), nullable=True)
    video_url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    view_count = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    shop = db.relationship("Shop", lazy=True)
    products = db.relationship(
        "Product",
        secondary=reel_products,
        order_by=reel_products.c.position,
        lazy=True,
    )

    def to_dict(self, with_products=True):
        data = {
            "id": self.id,
            "shopId": self.shop_id,
            "shopName": self.shop.name if self.shop else None,
            "shopLogoUrl": self.shop.logo_url if self.shop else None,
            "caption": self.caption,
            "videoUrl": self.video_url,
            "thumbnailUrl": self.thumbnail_url,
            "durationSeconds": self.duration_seconds,
            "viewCount": self.view_count,
            "productCount": len(self.products),
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
        if with_products:
            data["products"] = [p.to_dict() for p in self.products]
        return data


# ============================================================
# DIVIX LIVE — livraisons & signalements
# ============================================================


class Delivery(db.Model):
    """Livraison d'une commande, prise en charge par un livreur.

    Reliée 1:1 à une commande. Les statuts suivent le trajet du colis :
    non affectée → affectée → récupérée → en livraison → livrée (ou échouée).
    Les changements de statut synchronisent le statut de la commande.
    """

    __tablename__ = "deliveries"

    STATUS_LABELS = {
        "unassigned": "À affecter",
        "assigned": "Affectée",
        "picked_up": "Récupérée",
        "delivering": "En livraison",
        "delivered": "Livrée",
        "failed": "Échouée",
    }

    # Statut de livraison -> statut de commande correspondant (synchro).
    ORDER_STATUS_SYNC = {
        "picked_up": "picked_up",
        "delivering": "delivering",
        "delivered": "delivered",
    }

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id"), nullable=False, unique=True
    )
    driver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(
        db.Enum(
            "unassigned",
            "assigned",
            "picked_up",
            "delivering",
            "delivered",
            "failed",
            name="delivery_status",
        ),
        nullable=False,
        default="unassigned",
    )
    fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    notes = db.Column(db.String(500), nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    picked_up_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    driver = db.relationship("User", lazy=True)

    def to_dict(self, with_order=False):
        data = {
            "id": self.id,
            "orderId": self.order_id,
            "driverId": self.driver_id,
            "driverName": self.driver.name if self.driver else None,
            "driverPhone": self.driver.phone if self.driver else None,
            "status": self.status,
            "statusLabel": self.STATUS_LABELS.get(self.status, self.status),
            "fee": float(self.fee) if self.fee is not None else 0.0,
            "notes": self.notes,
            "assignedAt": self.assigned_at.isoformat() if self.assigned_at else None,
            "pickedUpAt": self.picked_up_at.isoformat()
            if self.picked_up_at
            else None,
            "deliveredAt": self.delivered_at.isoformat()
            if self.delivered_at
            else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
        if with_order and self.order is not None:
            data["order"] = self.order.to_dict()
        return data


class SellerApplication(db.Model):
    """Candidature « Devenir vendeur » (KYC) soumise par un acheteur.

    Regroupe les infos de la future boutique, ses visuels et les pièces
    d'identité. Validée ou refusée par l'administration : à l'approbation,
    le compte passe acheteur -> commerçant et la boutique est créée.
    """

    __tablename__ = "seller_applications"

    STATUS_LABELS = {
        "pending": "En attente",
        "approved": "Approuvée",
        "rejected": "Refusée",
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    shop_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    cover_url = db.Column(db.String(500), nullable=True)
    id_type = db.Column(
        db.Enum("cni", "passport", name="id_document_type"), nullable=False
    )
    id_front_url = db.Column(db.String(500), nullable=True)
    id_back_url = db.Column(db.String(500), nullable=True)
    selfie_url = db.Column(db.String(500), nullable=True)
    status = db.Column(
        db.Enum("pending", "approved", "rejected", name="seller_app_status"),
        nullable=False,
        default="pending",
    )
    terms_version = db.Column(db.String(20), nullable=True)
    review_note = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "shopName": self.shop_name,
            "category": self.category,
            "city": self.city,
            "logoUrl": self.logo_url,
            "coverUrl": self.cover_url,
            "idType": self.id_type,
            "idFrontUrl": self.id_front_url,
            "idBackUrl": self.id_back_url,
            "selfieUrl": self.selfie_url,
            "status": self.status,
            "statusLabel": self.STATUS_LABELS.get(self.status, self.status),
            "termsVersion": self.terms_version,
            "reviewNote": self.review_note,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class DriverApplication(db.Model):
    """Candidature « Devenir livreur » (KYC) soumise par un utilisateur.

    Regroupe la zone de travail, les informations du véhicule (immatriculation
    de la moto, vignette, assurance) et les pièces d'identité. Validée ou
    refusée par l'administration : à l'approbation, le compte passe livreur.
    """

    __tablename__ = "driver_applications"

    STATUS_LABELS = {
        "pending": "En attente",
        "approved": "Approuvée",
        "rejected": "Refusée",
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    city = db.Column(db.String(100), nullable=True)
    plate_number = db.Column(db.String(30), nullable=False)
    vignette_url = db.Column(db.String(500), nullable=True)
    insurance_url = db.Column(db.String(500), nullable=True)
    id_type = db.Column(
        db.Enum("cni", "passport", name="driver_id_document_type"),
        nullable=False,
    )
    id_front_url = db.Column(db.String(500), nullable=True)
    id_back_url = db.Column(db.String(500), nullable=True)
    selfie_url = db.Column(db.String(500), nullable=True)
    status = db.Column(
        db.Enum("pending", "approved", "rejected", name="driver_app_status"),
        nullable=False,
        default="pending",
    )
    terms_version = db.Column(db.String(20), nullable=True)
    review_note = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "city": self.city,
            "plateNumber": self.plate_number,
            "vignetteUrl": self.vignette_url,
            "insuranceUrl": self.insurance_url,
            "idType": self.id_type,
            "idFrontUrl": self.id_front_url,
            "idBackUrl": self.id_back_url,
            "selfieUrl": self.selfie_url,
            "status": self.status,
            "statusLabel": self.STATUS_LABELS.get(self.status, self.status),
            "termsVersion": self.terms_version,
            "reviewNote": self.review_note,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class Report(db.Model):
    """Signalement d'un contenu (produit, live, boutique ou utilisateur)
    par un utilisateur, à traiter par l'administration."""

    __tablename__ = "reports"

    STATUS_LABELS = {
        "open": "Ouvert",
        "reviewing": "En cours",
        "resolved": "Résolu",
        "dismissed": "Rejeté",
    }

    TARGET_LABELS = {
        "product": "Produit",
        "live": "Live",
        "shop": "Boutique",
        "user": "Utilisateur",
    }

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    target_type = db.Column(
        db.Enum("product", "live", "shop", "user", name="report_target"),
        nullable=False,
    )
    target_id = db.Column(db.String(30), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(1000), nullable=True)
    status = db.Column(
        db.Enum("open", "reviewing", "resolved", "dismissed", name="report_status"),
        nullable=False,
        default="open",
    )
    created_at = db.Column(db.DateTime, default=_utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    reporter = db.relationship("User", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "reporterId": self.reporter_id,
            "reporterName": self.reporter.name if self.reporter else None,
            "targetType": self.target_type,
            "targetTypeLabel": self.TARGET_LABELS.get(
                self.target_type, self.target_type
            ),
            "targetId": self.target_id,
            "reason": self.reason,
            "message": self.message,
            "status": self.status,
            "statusLabel": self.STATUS_LABELS.get(self.status, self.status),
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "resolvedAt": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class SubscriptionPayment(db.Model):
    """Paiement d'abonnement vendeur (préparé pour un fournisseur mobile money).

    Le flux : création d'un paiement `pending` -> le fournisseur confirme via
    webhook -> statut `success` et l'abonnement de la boutique est prolongé.
    Tant qu'aucun fournisseur n'est branché, un paiement peut être validé
    manuellement par l'administration.
    """

    __tablename__ = "subscription_payments"

    STATUS_LABELS = {
        "pending": "En attente",
        "success": "Payé",
        "failed": "Échoué",
        "cancelled": "Annulé",
    }

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    plan = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    provider = db.Column(db.String(30), nullable=True)  # cinetpay, wave, manual…
    reference = db.Column(db.String(100), nullable=True)  # id transaction fournisseur
    status = db.Column(
        db.Enum(
            "pending", "success", "failed", "cancelled",
            name="subscription_payment_status",
        ),
        nullable=False,
        default="pending",
    )
    days = db.Column(db.Integer, nullable=False, default=30)
    created_at = db.Column(db.DateTime, default=_utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)

    shop = db.relationship("Shop", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "shopId": self.shop_id,
            "plan": self.plan,
            "amount": float(self.amount) if self.amount is not None else 0.0,
            "provider": self.provider,
            "reference": self.reference,
            "status": self.status,
            "statusLabel": self.STATUS_LABELS.get(self.status, self.status),
            "days": self.days,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "paidAt": self.paid_at.isoformat() if self.paid_at else None,
        }


# ============================================================
# DIVIX — Notifications push (jetons d'appareils FCM)
# ============================================================


class DeviceToken(db.Model):
    """Jeton FCM d'un appareil, rattaché à un utilisateur, pour les
    notifications push. Un même jeton peut changer d'utilisateur
    (réinstallation, reconnexion) : il est alors réaffecté."""

    __tablename__ = "device_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    token = db.Column(db.String(255), nullable=False, unique=True)
    platform = db.Column(db.String(20), nullable=True)  # android / ios / web
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "platform": self.platform,
        }


# ============================================================
# DIVIX — Feature flags (activer/désactiver des fonctionnalités)
# ============================================================


class FeatureFlag(db.Model):
    """Interrupteur d'une fonctionnalité. Seules les valeurs qui diffèrent du
    défaut sont stockées ; le reste suit DEFAULT_FLAGS (voir app/features.py)."""

    __tablename__ = "feature_flags"

    key = db.Column(db.String(60), primary_key=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)


# ============================================================
# DIVIX — Avis & notes produits
# ============================================================


class Review(db.Model):
    """Avis d'un acheteur sur un produit (note 1-5 + commentaire).

    Un seul avis par utilisateur et par produit (mis à jour si re-soumis).
    La note et le nombre d'avis du produit sont recalculés à chaque écriture
    (champs dénormalisés products.rating / products.review_count).
    """

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.String(30), db.ForeignKey("products.id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1..5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    user = db.relationship("User", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("product_id", "user_id", name="uq_review_user"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "productId": self.product_id,
            "userId": self.user_id,
            "userName": self.user.name if self.user else "Utilisateur",
            "rating": self.rating,
            "comment": self.comment,
            "date": self.created_at.isoformat() if self.created_at else None,
        }
