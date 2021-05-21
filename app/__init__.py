import os
import logging
from config import Config
from flask_cors import CORS
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from logging.handlers import RotatingFileHandler
from flask_login import LoginManager
from importlib import import_module
from flask_moment import Moment
from flask_uploads import IMAGES, UploadSet, configure_uploads
from flask import Blueprint
from celery import Celery
from flask_socketio import SocketIO
from celery_once import QueueOnce

# instantiate the app
app = Flask(__name__)
app.config.from_object(Config)


db = SQLAlchemy()
login_manager = LoginManager()

photos = UploadSet("photos", IMAGES)
configure_uploads(app, photos)

# enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

moment = Moment(app)


# Configure celery configuration
def make_celery(app):

    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    celery.conf.ONCE = {
        'backend': 'celery_once.backends.Redis',
        'settings': {
            'url': app.config['CELERY_BROKER_URL'],
            'default_timeout': 60 * 60
        }
    }

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    class ContextQueueOnce(QueueOnce):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super(ContextQueueOnce, self).__call__(*args, **kwargs)

    celery.QueueOnce = ContextQueueOnce

    return celery


celery = make_celery(app)

socketio = SocketIO(app, message_queue=app.config['CELERY_BROKER_URL'])

# Start logging
if not os.path.exists("logs"):
    os.mkdir("logs")

file_handler = RotatingFileHandler(
    "logs/project.log",
    maxBytes=1000000,
    backupCount=3
)

file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    )
)

file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)

app.logger.info("STARTED project")
app.logger.info("DEBUG = " + app.config["DEBUG"])
app.logger.info("DBMS  = " + app.config["SQLALCHEMY_DATABASE_URI"])

db.init_app(app)
login_manager.init_app(app)

blueprint = Blueprint(
    "home_blueprint",
    __name__,
    url_prefix="",
    template_folder="templates",
    static_folder="static",
)

module = import_module("app.routes")
app.register_blueprint(module.blueprint)


from app import routes, models, util
