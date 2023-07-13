from time import time
import jwt
from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import LargeBinary, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app import app, db, login_manager
from app.util import hash_pass


class User(db.Model, UserMixin):

    __tablename__ = "User"

    id = Column(Integer, primary_key=True)

    username = Column(String(32), unique=True)
    email = Column(String(128), unique=True)
    password = Column(LargeBinary)

    first_name = Column(String(32))
    last_name = Column(String(32))

    profileimage = Column(String(256), default="profile_template.png")

    city = Column(String(32))
    country = Column(String(32))
    timezone = Column(String(128))

    primary_profile_id = Column(Integer, ForeignKey("Settings.id"))

    def __init__(self, **kwargs):

        for property, value in kwargs.items():

            if hasattr(value, "__iter__") and not isinstance(value, str):
                value = value[0]

            if property == "password":
                value = hash_pass(value)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)

    def get_reset_password_token(self, expires_in=43200):

        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):

        try:

            id = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']

        except Exception as e:

            app.logger.info(e)
            return

        return User.query.get(id)

    def set_password(self, password_value):
        self.password = hash_pass(password_value)


class Settings(db.Model):

    __tablename__ = "Settings"

    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    description = Column(String(128))

    is_primary = relationship("User")

    watering_start_at = Column(String(32), default="14:00")
    water_duration_minutes = Column(String(32), default="60")

    latitude = Column(String(32))
    longitude = Column(String(32))
    owm_apikey = Column(String(128))

    city = Column(String(32))
    country = Column(String(32))
    timezone = Column(String(128))

    schedule_watering = Column(String(32), default="eod")

    skip_rained_today = Column(String(32), default="1")
    skip_rained_yesterday = Column(String(32), default="1")
    skip_watered_today = Column(String(32), default="1")
    skip_watered_yesterday = Column(String(32), default="1")

    telegram_token = Column(String(128))
    telegram_chat_id = Column(String(128))

    def __repr__(self):
        return str(self.name)


class Watering(db.Model, UserMixin):

    __tablename__ = "Watering"

    id = Column(Integer, primary_key=True)
    water_start_time = Column(DateTime)
    water_end_time = Column(DateTime)
    water_duration_minutes = Column(String(32))
    adhoc_request = Column(String(32), default="0")
    status = Column(String(32))


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):

    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()

    return user if user else None
