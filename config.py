import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):

    SECRET_KEY = os.environ.get("SECRET_KEY") or "123456"

    LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL") or "DEBUG"
    DEBUG = os.environ.get("DEBUG") or True
    FLASK_ENV = os.environ.get("FLASK_ENV") or "development"

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "project.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    DEBUG_TB_INTERCEPT_REDIRECTS = False

    UPLOADED_PHOTOS_DEST = os.path.join(basedir, "app/static/uploads")
    UPLOADED_FILES_ALLOW = ["jpg", "png"]

    DEMO_MODE = os.environ.get("DEMO_MODE") or True

    CELERY_BROKER_URL = os.environ.get(
        "CELERY_BROKER_URL"
    ) or 'redis://192.168.10.11:6379/0'

    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND"
    ) or 'redis://192.168.10.11:6379/0'
