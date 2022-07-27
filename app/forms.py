from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, PasswordField
from wtforms.validators import EqualTo, Email, DataRequired


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        id="username_login",
        validators=[DataRequired()]
    )
    password = PasswordField(
        "Password",
        id="pwd_login",
        validators=[DataRequired()]
    )


class CreateAccountForm(FlaskForm):
    username = StringField(
        "Username",
        id="username_create",
        validators=[DataRequired()]
    )
    email = StringField(
        "Email",
        id="email_create",
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Password",
        id="pwd_create",
        validators=[DataRequired()]
    )


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(
        "Email",
        id="email_create",
        validators=[DataRequired(), Email()]
    )


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "Password",
        id="pwd_create",
        validators=[DataRequired()]
    )
    password_confirm = PasswordField(
        "Repeat Password",
        id="pwd_create_confirm",
        validators=[DataRequired(), EqualTo(
            'password',
            message="Passwords must be the same."
        )]
    )


class UploadProfileImage(FlaskForm):
    file = FileField()
