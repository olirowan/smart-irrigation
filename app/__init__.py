import os
import eventlet

# eventlet.monkey_patch()

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
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
from celery_once import QueueOnce
from apscheduler.schedulers.background import BackgroundScheduler
import pymysql
pymysql.install_as_MySQLdb()

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

csrf = CSRFProtect(app)

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
            'default_timeout': 60 * 30
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



task_schedule = BackgroundScheduler(daemon=True)
task_schedule.start()

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
app.logger.info("DEBUG = " + str(app.config["DEBUG"]))
app.logger.info("DBMS  = " + str(app.config["SQLALCHEMY_DATABASE_URI"]))

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('geventwebsocket.handler').setLevel(logging.ERROR)

db.init_app(app)
login_manager.init_app(app)

socketio = SocketIO(app, logger=False, engineio_logger=False, message_queue=app.config['CELERY_BROKER_URL'])

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
