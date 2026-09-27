import os
from datetime import timedelta
from urllib.parse import quote_plus

from dotenv import load_dotenv


# ============================================================
# CHARGEMENT DU .env
# ============================================================

# Charge le fichier .env situé à la racine du projet.
load_dotenv()


# ============================================================
# VARIABLES ENVIRONNEMENT
# ============================================================

DB_PORT = os.environ.get("DB_PORT", "3306")
DB_HOST = os.environ.get("DB_HOST", "")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "")


# ============================================================
# URL DE BASE DE DONNÉES
# ============================================================

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

else:
    if not DB_HOST:
        raise RuntimeError(
            "DB_HOST n'est pas configuré dans le fichier .env"
        )

    if not DB_USER:
        raise RuntimeError(
            "DB_USER n'est pas configuré dans le fichier .env"
        )

    if not DB_NAME:
        raise RuntimeError(
            "DB_NAME n'est pas configuré dans le fichier .env"
        )

    # Le mot de passe peut éventuellement être vide,
    # notamment pour certaines installations locales.
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://"
        f"{quote_plus(DB_USER)}:"
        f"{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/"
        f"{DB_NAME}"
        f"?charset=utf8mb4"
    )


# ============================================================
# CONFIGURATION FLASK
# ============================================================

class Config:

    # --------------------------------------------------------
    # Base de données
    # --------------------------------------------------------

    DB_PORT = DB_PORT
    DB_HOST = DB_HOST
    DB_USER = DB_USER
    DB_PASSWORD = DB_PASSWORD
    DB_NAME = DB_NAME

    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --------------------------------------------------------
    # JWT
    # --------------------------------------------------------

    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY",
        "change-me-in-production",
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        days=7
    )

    # --------------------------------------------------------
    # Redis
    # --------------------------------------------------------

    REDIS_URL = os.environ.get(
        "REDIS_URL",
        "redis://localhost:6379/0",
    )

    # --------------------------------------------------------
    # RabbitMQ
    # --------------------------------------------------------

    RABBITMQ_URL = os.environ.get(
        "RABBITMQ_URL",
        "amqp://guest:guest@localhost:5672/%2F",
    )

    RABBITMQ_QUEUE = os.environ.get(
        "RABBITMQ_QUEUE",
        "divix.events",
    )

    # --------------------------------------------------------
    # Streaming vidéo - Agora
    # --------------------------------------------------------

    AGORA_APP_ID = os.environ.get(
        "AGORA_APP_ID",
        "",
    )

    AGORA_APP_CERTIFICATE = os.environ.get(
        "AGORA_APP_CERTIFICATE",
        "",
    )

    AGORA_TOKEN_TTL = int(
        os.environ.get(
            "AGORA_TOKEN_TTL",
            "3600",
        )
    )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    JSON_SORT_KEYS = False

    # --------------------------------------------------------
    # Uploads
    # --------------------------------------------------------

    UPLOAD_DIR = os.environ.get(
        "UPLOAD_DIR",
        "uploads",
    )

    # Maximum global d'une requête HTTP :
    # 8 Mo.
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024