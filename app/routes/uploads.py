"""Upload d'images : visuels de boutique/produits et pièces d'identité.

Stockage : Cloudinary si configuré (persistant), sinon repli sur le disque
local (dossier UPLOAD_DIR, éphémère sur Render — utile en dev).

Configuration Cloudinary (variables d'environnement) :
  - CLOUDINARY_URL = cloudinary://<api_key>:<api_secret>@<cloud_name>
    (une seule variable, format fourni par le tableau de bord Cloudinary)
  ou séparément :
  - CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
"""

import os
import uuid

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

uploads_bp = Blueprint("uploads", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "heic"}
MAX_BYTES = 8 * 1024 * 1024  # 8 Mo
CLOUDINARY_FOLDER = "divix"

_cloudinary_ready = None


def _cloudinary():
    """Configure et renvoie le module cloudinary si des identifiants existent,
    sinon None."""
    global _cloudinary_ready
    if _cloudinary_ready is not None:
        return _cloudinary_ready or None
    try:
        import cloudinary

        url = os.environ.get("CLOUDINARY_URL")
        cloud = os.environ.get("CLOUDINARY_CLOUD_NAME")
        key = os.environ.get("CLOUDINARY_API_KEY")
        secret = os.environ.get("CLOUDINARY_API_SECRET")
        if url:
            cloudinary.config()  # lit CLOUDINARY_URL depuis l'environnement
            _cloudinary_ready = cloudinary
        elif cloud and key and secret:
            cloudinary.config(
                cloud_name=cloud, api_key=key, api_secret=secret, secure=True
            )
            _cloudinary_ready = cloudinary
        else:
            _cloudinary_ready = False
    except Exception:
        _cloudinary_ready = False
    return _cloudinary_ready or None


def _upload_dir():
    path = current_app.config.get("UPLOAD_DIR", "uploads")
    os.makedirs(path, exist_ok=True)
    return path


def _ext_ok(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@uploads_bp.post("/api/uploads")
@jwt_required()
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier envoyé"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Fichier vide"}), 400
    if not _ext_ok(file.filename):
        return jsonify({"error": "Format non supporté (jpg, png, webp, heic)"}), 400

    cld = _cloudinary()
    if cld is not None:
        try:
            result = cld.uploader.upload(
                file,
                folder=CLOUDINARY_FOLDER,
                resource_type="image",
            )
            return (
                jsonify(
                    {
                        "url": result["secure_url"],
                        "name": result.get("public_id"),
                        "provider": "cloudinary",
                    }
                ),
                201,
            )
        except Exception:
            return jsonify({"error": "Échec de l'envoi de l'image."}), 502

    # Repli : stockage local (dev / Cloudinary non configuré).
    ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(_upload_dir(), name))
    url = request.host_url.rstrip("/") + "/uploads/" + name
    return jsonify({"url": url, "name": name, "provider": "local"}), 201


@uploads_bp.get("/uploads/<path:name>")
def serve_upload(name):
    return send_from_directory(_upload_dir(), name)
