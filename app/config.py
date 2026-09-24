import os
from datetime import timedelta
from urllib.parse import quote_plus


class Config:
    DB_PORT = os.environ.get("DB_PORT")
    DB_HOST = os.environ.get("DB_HOST")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_NAME = os.environ.get("DB_NAME")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # Streaming vidéo (Agora) — laissés vides tant que le compte n'est pas créé.
    AGORA_APP_ID = os.environ.get("AGORA_APP_ID", "")
    AGORA_APP_CERTIFICATE = os.environ.get("AGORA_APP_CERTIFICATE", "")
    # Durée de validité d'un jeton de salle (secondes).
    AGORA_TOKEN_TTL = int(os.environ.get("AGORA_TOKEN_TTL", "3600"))

    JSON_SORT_KEYS = False

    # Upload de fichiers (visuels boutique, pièces d'identité KYC).
    UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 Mo par requête
