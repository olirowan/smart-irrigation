import os
import redis
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):

    SECRET_KEY = os.environ.get("SECRET_KEY") or "123456"

    DEBUG = os.environ.get("DEBUG") or True
    FLASK_ENV = os.environ.get("FLASK_ENV") or "development"
    LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL") or "DEBUG"

    TIMEZONE = os.environ.get(
        "TIMEZONE"
    ) or 'Europe/London'

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "project.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE") or False
    REMEMBER_COOKIE_SECURE = os.environ.get("REMEMBER_COOKIE_SECURE") or False
    SESSION_COOKIE_HTTPONLY = os.environ.get(
        "SESSION_COOKIE_HTTPONLY"
    ) or False

    REMEMBER_COOKIE_HTTPONLY = os.environ.get(
        "REMEMBER_COOKIE_HTTPONLY"
    ) or False

    UPLOADED_PHOTOS_DEST = os.path.join(basedir, "app/static/uploads")
    UPLOADED_FILES_ALLOW = ["jpg", "png"]

    DEMO_MODE = os.environ.get("DEMO_MODE") or True

    CELERY_BROKER_URL = os.environ.get(
            "CELERY_BROKER_URL"
        ) or 'redis://localhost:6379/0'

    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND"
    ) or 'redis://localhost:6379/0'

    CELERY_CONFIG = {
        "broker_url": os.environ.get(
            "CELERY_BROKER_URL"
        ),
        "result_backend": os.environ.get(
            "CELERY_RESULT_BACKEND"
        ),
        "timezone": TIMEZONE,
        "imports": (
            'app.watering',
        ),
    }

    SESSION_TYPE = os.environ.get("SESSION_TYPE") or 'filesystem'
    SESSION_PERMANENT = os.environ.get("SESSION_PERMANENT") or False
    SESSION_USE_SIGNER = os.environ.get("SESSION_USE_SIGNER") or True

    if SESSION_TYPE == "redis":
        SESSION_REDIS = redis.from_url(os.environ.get("SESSION_REDIS"))
