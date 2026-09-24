from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .extensions import db, jwt
from .routes.auth import auth_bp
from .routes.cart import cart_bp
from .routes.categories import categories_bp
from .routes.deliveries import deliveries_bp
from .routes.favorites import favorites_bp
from .routes.health import health_bp
from .routes.lives import lives_bp
from .routes.orders import orders_bp
from .routes.products import products_bp
from .routes.reports import reports_bp
from .routes.seller_applications import seller_apps_bp
from .routes.shops import shops_bp
from .routes.uploads import uploads_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(shops_bp)
    app.register_blueprint(lives_bp)
    app.register_blueprint(deliveries_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(seller_apps_bp)
    app.register_blueprint(uploads_bp)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Ressource introuvable"}), 404

    @app.errorhandler(500)
    def server_error(_error):
        return jsonify({"error": "Erreur interne du serveur"}), 500

    @jwt.unauthorized_loader
    def unauthorized(_reason):
        return jsonify({"error": "Authentification requise"}), 401

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return jsonify({"error": "Jeton invalide"}), 401

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return jsonify({"error": "Jeton expiré"}), 401

    return app
