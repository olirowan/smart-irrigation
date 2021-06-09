from flask import render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required, login_user, logout_user
from app import blueprint, app
from flask_socketio import emit
import hashlib
import datetime
import pytz
import json
import traceback
import types
from app import db, login_manager, photos, socketio
from app.forms import LoginForm, CreateAccountForm
from app.forms import ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.util import verify_pass
from app.tasks import water_plants
from pathlib import Path
from app.weather import get_current_weather, owm_icon_mapping, get_city_country
from app.weather import get_last_rain_date, get_next_rain_date
from app.weather import get_last_water_date, get_next_water_date


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

    if current_user.city is None or current_user.country is None or current_user.timezone is None:

        current_weather = types.SimpleNamespace()
        current_weather.detailed_status = "Location Setting Required"
        current_date = datetime.datetime.now(pytz.timezone("Europe/London"))
        weather_icon = "fas fa-ban"
        last_rain_date = "API Key Required"
        next_rain_date = "API Key Required"
        last_water_date = "N/A"
        next_water_date = "API Key Required"
        last_water_duration = "0"

    else:

        try:

            current_weather = get_current_weather(
                current_user.city,
                current_user.country
            )

            current_date = datetime.datetime.now(
                pytz.timezone(current_user.timezone)
            )

            if current_date.hour > 6 and current_date.hour < 20:

                prefix = "wi wi-day-"
            else:
                prefix = "wi wi-night-"

            weather_icon = prefix + owm_icon_mapping(
                current_weather.weather_code
            )

            last_rain_date = get_last_rain_date(
                current_user.latitude,
                current_user.longitude
            )
            next_rain_date = get_next_rain_date(
                current_user.latitude,
                current_user.longitude
            )
            last_water_date, last_water_duration = get_last_water_date()
            next_water_date = get_next_water_date(
                current_user.latitude,
                current_user.longitude
            )

        except Exception as e:

            app.logger.error(e)
            app.logger.info(traceback.format_exc())
            current_weather = types.SimpleNamespace()
            current_weather.detailed_status = "Invalid API Key"
            current_date = datetime.datetime.now(
                pytz.timezone("Europe/London")
            )
            weather_icon = "fas fa-ban"
            last_rain_date = "Invalid API Key"
            next_rain_date = "Invalid API Key"
            last_water_date = "N/A"
            last_water_duration = "N/A"
            next_water_date = "Invalid API Key"

    return render_template(
        "dashboard.html",
        weather=current_weather,
        current_date=current_date,
        weather_icon=weather_icon,
        last_rain_date=last_rain_date,
        next_rain_date=next_rain_date,
        last_water_date=last_water_date,
        last_water_duration=last_water_duration,
        next_water_date=next_water_date,
        segment=active_icon
    )


@blueprint.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    active_icon = "settings"

    timezones = pytz.common_timezones

    if request.method == "POST":

        latitude_value = request.form.get("latitude")
        longitude_value = request.form.get("longitude")

        if latitude_value is not None and longitude_value is not None and (latitude_value != current_user.latitude or longitude_value != current_user.longitude):

            location_info = json.dumps(get_city_country(latitude_value, longitude_value))


            if "city" in json.loads(location_info)["address"]:

                current_user.city = json.loads(location_info)["address"]["city"]
            else:

                current_user.city = json.loads(location_info)["address"]["state"]

            current_user.country = json.loads(location_info)["address"]["country"]

        current_user.first_name = request.form.get("first_name")
        current_user.last_name = request.form.get("last_name")
        current_user.owm_apikey = request.form.get("apikey")
        current_user.timezone = request.form.get("timezone")
        current_user.latitude = latitude_value
        current_user.longitude = longitude_value

        current_user.water_duration_minutes = request.form.get("water_duration_minutes")
        current_user.schedule_watering = request.form.get("schedule_watering")
        current_user.skip_rained_today = request.form.get("skip_rained_today")
        current_user.skip_rained_yesterday = request.form.get("skip_rained_yesterday")
        current_user.skip_watered_today = request.form.get("skip_watered_today")
        current_user.skip_watered_yesterday = request.form.get("skip_watered_yesterday")

        current_user.watering_start_at = request.form.get("water_start_time")
        log_me = request.form.get("water_start_time")
        app.logger.info(log_me)

        db.session.commit()

        return redirect(url_for("home_blueprint.settings"))

    return render_template(
        "settings.html",
        timezones=timezones,
        segment=active_icon
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
            app.logger.info("Password reset token requested for: " + str(user.email))
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


# event handler for connection where the client\
# recieves a confirmation message upon the connection to the socket
@socketio.on("connection", namespace="/water")
def confirmation_message(message):

    emit("confirmation", {
        "connection_confirmation": message["connection_confirmation"]
    })


@socketio.on("water_plants_socket", namespace="/water")
def water_plants_socket(duration):

    command = duration.get("duration")

    if command == "cancel_duration":
        app.logger.info("Some logic to cancel any watering")

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
        water_plants.apply_async(time_seconds, 1)

    else:
        app.logger.info("wtf")


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
