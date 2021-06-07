from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField
from wtforms.validators import EqualTo, Email, DataRequired


class LoginForm(FlaskForm):
    username = TextField("Username", id="username_login", validators=[DataRequired()])
    password = PasswordField("Password", id="pwd_login", validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = TextField("Username", id="username_create", validators=[DataRequired()])
    email = TextField("Email", id="email_create", validators=[DataRequired(), Email()])
    password = PasswordField("Password", id="pwd_create", validators=[DataRequired()])


class ResetPasswordRequestForm(FlaskForm):
    email = TextField("Email", id="email_create", validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", id="pwd_create", validators=[DataRequired()])
    password_confirm = PasswordField("Repeat Password",  id="pwd_create_confirm", validators=[DataRequired(), EqualTo('password', message="Passwords must be the same.")])