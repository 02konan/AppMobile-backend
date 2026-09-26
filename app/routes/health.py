import pika
from flask import Blueprint, current_app, jsonify

from ..extensions import get_redis

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@health_bp.get("/health/dependencies")
def dependencies_health():
    dependencies = {}

    try:
        get_redis().ping()
        dependencies["redis"] = "ok"
    except Exception:
        dependencies["redis"] = "error"

    try:
        connection = pika.BlockingConnection(
            pika.URLParameters(current_app.config["RABBITMQ_URL"])
        )
        connection.close()
        dependencies["rabbitmq"] = "ok"
    except Exception:
        dependencies["rabbitmq"] = "error"

    status_code = 200 if all(value == "ok" for value in dependencies.values()) else 503
    return (
        jsonify(
            {
                "status": "ok" if status_code == 200 else "degraded",
                "dependencies": dependencies,
            }
        ),
        status_code,
    )
