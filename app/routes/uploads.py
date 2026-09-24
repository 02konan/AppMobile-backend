"""Upload de fichiers (images) : visuels de boutique et pièces d'identité.

Les fichiers sont stockés sur le disque du serveur (dossier UPLOAD_DIR) et
servis via /uploads/<nom>. Les noms sont aléatoires (uuid) donc non devinables.

NB : sur un hébergement à disque éphémère (Render gratuit), les fichiers ne
survivent pas aux redémarrages — OK pour tester. Pour la prod, migrer vers un
stockage persistant (S3 / Cloudinary) et servir les pièces d'identité derrière
une authentification / URL signée.
"""

import os
import uuid

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

uploads_bp = Blueprint("uploads", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "heic"}
MAX_BYTES = 8 * 1024 * 1024  # 8 Mo


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

    ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(_upload_dir(), name)
    file.save(path)

    # URL absolue servie par le backend (hors préfixe /api).
    url = request.host_url.rstrip("/") + "/uploads/" + name
    return jsonify({"url": url, "name": name}), 201


@uploads_bp.get("/uploads/<path:name>")
def serve_upload(name):
    return send_from_directory(_upload_dir(), name)
