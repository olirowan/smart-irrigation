import pytz
import hashlib
import datetime
from pathlib import Path

from flask import render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required, login_user, logout_user
from flask_socketio import emit

from app import app, blueprint, db, login_manager, photos, socketio
from app.dashboard import get_dashboard_data
from app.forms import LoginForm, CreateAccountForm, ResetPasswordRequestForm
from app.forms import ResetPasswordForm, UploadProfileImage
from app.models import User, Settings
from app.settings_profile import create_or_update_settings_profile
from app.util import verify_pass, get_celery_worker_status
from app.watering import water_plants, cancel_water_plants


@blueprint.route("/index")
@login_required
def index():

    return render_template("dashboard.html")


@blueprint.route("/")
def route_default():
    return redirect(url_for("home_blueprint.login"))


@blueprint.route("/dashboard")
@login_required
def dashboard():

    active_icon = "dashboard"

    dashboard_data = get_dashboard_data()

    return render_template(
        "dashboard.html",
        dashboard_data=dashboard_data,
        segment=active_icon
    )


@blueprint.route("/settings", methods=["GET"])
@login_required
def settings():

    active_icon = "settings"

    settings_profiles = Settings.query.filter().order_by(Settings.name)

    return render_template(
        "settings.html",
        settings_profiles=settings_profiles,
        segment=active_icon
    )


@blueprint.route("/add_settings_profile", methods=["GET", "POST"])
@login_required
def add_settings_profile():

    active_icon = "settings"

    timezones = pytz.common_timezones

    if request.method == "POST":

        name = request.form.get("name")

        if Settings.query.filter_by(name=name).first() is not None:

            flash('Error: the name "' + name + '" is already in use.')

            return render_template(
                "settings_profile.html",
                settings_profile=settings_profile,
                timezones=timezones,
                segment=active_icon,
            )

        create_or_update_settings_profile(request, name)

        return redirect(url_for("home_blueprint.settings"))

    return render_template(
        "settings_profile.html",
        timezones=timezones,
        settings_profile="",
        edit=False,
        segment=active_icon,
    )


@blueprint.route("/settings/<name>", methods=["GET", "POST"])
@login_required
def settings_profile(name):

    active_icon = "settings"
    timezones = pytz.common_timezones
    hidden_apikey = None
    hidden_telegram_token = None

    settings_profile = Settings.query.filter_by(name=name).first_or_404()

    if request.method == "POST":

        new_name = request.form.get("name")

        if name != new_name:

            if Settings.query.filter_by(name=new_name).first() is not None:

                flash('Error: the name "' + new_name + '" is already in use.')

                return render_template(
                    "settings_profile.html",
                    settings_profile=settings_profile,
                    timezones=timezones,
                    segment=active_icon,
                )

        create_or_update_settings_profile(request, name)

        return redirect(url_for("home_blueprint.settings"))

    if settings_profile.owm_apikey is not None:

        hidden_apikey = (
            str(settings_profile.owm_apikey)[:12] + ("*" * 16)
        )

    if settings_profile.telegram_token is not None:

        hidden_telegram_token = (
            str(settings_profile.telegram_token)[:12] + ("*" * 16)
        )

    return render_template(
        "settings_profile.html",
        timezones=timezones,
        segment=active_icon,
        settings_profile=settings_profile,
        edit=True,
        hidden_apikey=hidden_apikey,
        hidden_telegram_token=hidden_telegram_token
    )


@blueprint.route("/settings/<name>/delete", methods=["POST"])
@login_required
def delete_settings_profile(name):

    settings_profile = Settings.query.filter_by(name=name).first_or_404()

    db.session.delete(settings_profile)

    db.session.commit()

    return redirect(url_for("home_blueprint.settings"))


@blueprint.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    image_form = UploadProfileImage()

    active_icon = "profile"

    timezones = pytz.common_timezones
    settings_profiles = Settings.query.filter().order_by(Settings.name)

    if current_user.primary_profile_id is not None:

        primary_profile = Settings.query.filter_by(
            id=current_user.primary_profile_id
        ).first()

        primary_profile_name = primary_profile.name

    else:

        primary_profile_name = None

    if request.method == "POST":

        settings_profile_data = Settings.query.filter_by(
            name=request.form.get("primary_profile")
        ).first()

        current_user.first_name = request.form.get("first_name")
        current_user.last_name = request.form.get("last_name")
        current_user.timezone = request.form.get("timezone")

        if settings_profile_data is not None:

            current_user.primary_profile_id = settings_profile_data.id

        db.session.commit()

        return redirect(url_for("home_blueprint.profile"))

    return render_template(
        "profile.html",
        form=image_form,
        timezones=timezones,
        segment=active_icon,
        settings_profiles=settings_profiles,
        primary_profile_name=primary_profile_name
    )


@blueprint.route("/profileimage", methods=["GET", "POST"])
@login_required
def profileimage():

    app.logger.info(request.files)

    if request.method == "POST" and "photo" in request.files:

        try:

            photo_file = request.files["photo"]
            photo_file_extension = Path(photo_file.filename).suffix

            photo_filename = str(hashlib.sha1(str(
                current_user.email).encode("utf-8") + str(
                current_user.id).encode("utf-8") + str(
                datetime.datetime.now().timestamp()).encode("utf-8")
                ).hexdigest()) + photo_file_extension

            photos.save(request.files["photo"], name=photo_filename)

            current_user.profileimage = photo_filename
            db.session.commit()

            flash("Profile image updated.")

            return redirect(url_for("home_blueprint.settings"))

        except Exception as e:
            app.logger.info("Exception: ", str(e))

    return redirect(url_for("home_blueprint.settings"))


# Login & Registration
@blueprint.route("/login", methods=["GET", "POST"])
def login():

    login_form = LoginForm(request.form)
    if "login" in request.form:

        # read form data
        username = request.form["username"]
        password = request.form["password"]

        # Locate user
        user = User.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for("home_blueprint.dashboard"))

        flash("Incorrect username or password.", category="text-danger")
        return render_template(
            "login.html",
            form=login_form
        )

    if not current_user.is_authenticated:
        return render_template("login.html", form=login_form)
    return redirect(url_for("home_blueprint.dashboard"))


@blueprint.route("/register", methods=["GET", "POST"])
def register():

    create_account_form = CreateAccountForm(request.form)
    if "register" in request.form:

        username = request.form["username"]
        email = request.form["email"]

        user = User.query.filter_by(username=username).first()
        if user:
            flash("This username cannot be used.", category="text-danger")
            return render_template(
                "register.html",
                success=False,
                form=create_account_form,
            )

        user = User.query.filter_by(email=email).first()
        if user:
            flash("This email cannot be used.", category="text-danger")
            return render_template(
                "register.html",
                success=False,
                form=create_account_form,
            )

        user = User(**request.form)
        db.session.add(user)
        db.session.commit()

        flash("Registration complete.", category="text-white")
        return redirect(url_for("home_blueprint.login"))

    else:
        return render_template("register.html", form=create_account_form)


@blueprint.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():

    if current_user.is_authenticated:
        return redirect(url_for("home_blueprint.dashboard"))

    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:

            token = user.get_reset_password_token()
            app.logger.info(
                "Password reset token requested for: " + str(user.email)
            )
            app.logger.info(token)

        flash("Reset instructions sent to email.", category="text-white")
        return redirect(url_for("home_blueprint.login"))

    return render_template("reset_password_request.html", form=form)


@blueprint.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):

    if current_user.is_authenticated:
        return redirect(url_for("home_blueprint.dashboard"))

    user = User.verify_reset_password_token(token)

    app.logger.info(user)

    if not user:
        app.logger.info("not user")
        return redirect(url_for("home_blueprint.dashboard"))

    form = ResetPasswordForm()

    app.logger.info(str(request.form))

    if "reset_password" in request.form:

        password = request.form["password"]
        password_confirm = request.form["password_confirm"]

        if password == password_confirm:

            user.set_password(password)
            db.session.commit()

            flash("Your password has been reset.", category="text-white")
            return redirect(url_for("home_blueprint.login"))

        elif password != password_confirm:

            flash("Passwords do not match.", category="text-danger")

    return render_template("reset_password.html", form=form)


@blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home_blueprint.login"))


@socketio.on("connection", namespace="/water")
def confirmation_message(message):

    celery_worker_status = get_celery_worker_status()

    if celery_worker_status["availability"] is not None:

        emit("confirmation", {
            "connection_confirmation": message["connection_confirmation"]
        })


@socketio.on("water_plants_socket", namespace="/water")
def water_plants_socket(duration):

    command = duration.get("duration")

    if command == "cancel_duration":
        cancel_water_plants.delay()

    elif command == "one_duration":
        water_plants.delay(60, 1)

    elif command == "five_duration":
        water_plants.delay(300, 1)

    elif command == "ten_duration":
        water_plants.delay(600, 1)

    elif command == "thirty_duration":
        water_plants.delay(1800, 1)

    elif command == "default_duration":

        time_seconds = int(current_user.water_duration_minutes) * 60
        water_plants.delay(time_seconds, 1)

    else:
        app.logger.info("Unexpected command passed.")


# Errors
@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("page-403.html"), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template("page-403.html"), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template("page-404.html"), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template("page-500.html"), 500
