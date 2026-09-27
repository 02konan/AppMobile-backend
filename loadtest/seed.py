"""Prépare une base de test pour le load-test Locust.

Crée une boutique validée, 10 produits et 20 acheteurs (mot de passe
"motdepasse1", téléphones +22507000000NN). À lancer avant Locust.

Exemple (base SQLite locale) :
  DATABASE_URL="sqlite:////tmp/divix_load.db" DB_USER=x DB_PASSWORD=x \
  DB_HOST=x DB_PORT=1 DB_NAME=x JWT_SECRET_KEY=loadtest SECRET_KEY=x \
  python loadtest/seed.py
"""

from app import create_app
from app.extensions import db
from app.models import Category, Product, Shop, User


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        if Category.query.get("mode") is None:
            db.session.add(Category(id="mode", name="Mode", icon="checkroom"))

        merchant = User.query.filter_by(phone="+2250100000001").first()
        if merchant is None:
            merchant = User(
                name="Vendeur Test", role="merchant", phone="+2250100000001"
            )
            merchant.set_password("motdepasse1")
            db.session.add(merchant)
            db.session.flush()

        shop = Shop.query.filter_by(user_id=merchant.id).first()
        if shop is None:
            shop = Shop(
                user_id=merchant.id,
                name="Boutique Test",
                status="validated",
                commune="Cocody",
            )
            db.session.add(shop)
            db.session.flush()

        for i in range(1, 11):
            pid = f"p{i}"
            if db.session.get(Product, pid) is None:
                db.session.add(
                    Product(
                        id=pid,
                        shop_id=shop.id,
                        category_id="mode",
                        name=f"Produit {i}",
                        description="Produit de test",
                        price=5000 + i * 1000,
                        image_url="https://example.com/p.jpg",
                        stock=100,
                        is_featured=(i <= 6),
                    )
                )

        for i in range(1, 21):
            phone = f"+22507000000{i:02d}"
            if User.query.filter_by(phone=phone).first() is None:
                u = User(name=f"Acheteur {i}", role="buyer", phone=phone)
                u.set_password("motdepasse1")
                db.session.add(u)

        db.session.commit()
        print(
            "seed OK — users:",
            User.query.count(),
            "produits:",
            Product.query.count(),
        )


if __name__ == "__main__":
    run()
