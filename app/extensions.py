from flask import current_app
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

db = SQLAlchemy()
jwt = JWTManager()


def init_redis(app):
	app.extensions["redis"] = Redis.from_url(
		app.config["REDIS_URL"],
		decode_responses=True,
	)


def get_redis():
	return current_app.extensions["redis"]
