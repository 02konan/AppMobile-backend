import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_USER = os.environ.get("DB_USER", "ecommerce_user")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "ecommerce_pass")
    DB_NAME = os.environ.get("DB_NAME", "ecommerce_app")

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    # Hash généré avec : python -c "from werkzeug.security import generate_password_hash as g; print(g('votre_mot_de_passe'))"
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")
