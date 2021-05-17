from flask_login import UserMixin
from sqlalchemy import Binary, Column, Integer, String
from app import db, login_manager
from app.util import hash_pass


class User(db.Model, UserMixin):

    __tablename__ = "User"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(Binary)
    first_name = Column(String)
    last_name = Column(String)
    city = Column(String)
    country = Column(String)
    timezone = Column(String)
    latitude = Column(String)
    longitude = Column(String)
    owm_apikey = Column(String)
    profileimage = Column(String, default="profile_template.png")
    water_duration_minutes = Column(String, default="60")
    schedule_watering = Column(String, default="eod")
    skip_rained_today = Column(String, default="1")
    skip_rained_yesterday = Column(String, default="1")
    skip_watered_today = Column(String, default="1")
    skip_watered_yesterday = Column(String, default="1")

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, "__iter__") and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == "password":
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    return user if user else None
