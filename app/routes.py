from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user, login_required, login_user, logout_user
from jinja2 import TemplateNotFound
from app import blueprint, app
from flask_socketio import emit, join_room
import hashlib
import datetime
import pytz
import json
import types
from app import db, login_manager, photos, celery, socketio
from app.forms import LoginForm, CreateAccountForm
from app.models import User
from app.util import verify_pass
from app.tasks import long_task, message_to_client, short_task
from pathlib import Path
from celery_once import AlreadyQueued
from app.weather import get_current_weather, owm_icon_mapping, get_city_country


@blueprint.route("/index")
@login_required
def index():

    return render_template("index.html", segment="index")


@blueprint.route("/<template>")
@login_required
def route_template(template):

    try:

        if not template.endswith(".html"):
            template += ".html"

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/FILE.html
        return render_template(template, segment=segment)

    except TemplateNotFound:
        return render_template("page-404.html"), 404

    except Exception as e:
        app.logger.critical(e, exc_info=True)
        return render_template("page-500.html"), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except:
        return None


@blueprint.route("/")
def route_default():
    return redirect(url_for("home_blueprint.login"))


@blueprint.route("/dashboard")
@login_required
def dashboard():

    if current_user.city is None or current_user.country is None or current_user.timezone is None:

        current_weather = types.SimpleNamespace()
        current_weather.detailed_status = "Location Setting Required"
        current_date = datetime.datetime.now(pytz.timezone("Europe/London"))
        weather_icon = "fas fa-ban"

    else:

        current_weather = get_current_weather(
            current_user.city,
            current_user.country
        )

        current_date = datetime.datetime.now(pytz.timezone(current_user.timezone))

        app.logger.info(current_date.hour)

        if current_date.hour > 6 and current_date.hour < 20:

            prefix = "wi wi-day-"
        else:
            prefix = "wi wi-night-"

        weather_icon = prefix + owm_icon_mapping(current_weather.weather_code)

    return render_template(
        "dashboard.html",
        weather=current_weather,
        current_date=current_date,
        weather_icon=weather_icon,
        segment=get_segment(request)
    )


@blueprint.route('/status/<task_id>')
def taskstatus(task_id):

    task = long_task.AsyncResult(task_id)

    if task.state == 'PENDING':

        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }

    elif task.state != 'FAILURE':

        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }

        if 'result' in task.info:
            response['result'] = task.info['result']
    else:

        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@blueprint.route('/longtask', methods=['GET', 'POST'])
def longtask():

    if request.method == "POST":

        try:
            task = long_task.apply_async()
            app.logger.info(task.task_id)

            return jsonify({}), 202, {'Location': url_for('home_blueprint.taskstatus',
                                                    task_id=task.id)}

        except AlreadyQueued:

            app.logger.info("Job is locked.")
            return jsonify({'message': 'Watering is already in progress'}), 409


@blueprint.route('/sockets')
def sockets():

    return render_template('sockets.html')


# event handler for connection where the client\
# recieves a confirmation message upon the connection to the socket
@socketio.on('connection', namespace='/test')
def confirmation_message(message):

    emit('confirmation', {'connection_confirmation': message['connection_confirmation']})


# event handler for name submission by the client
@socketio.on('submit_name', namespace='/test')
def name_handler(message):

    session_id = request.sid
    roomstr = session_id
    join_room(roomstr)
    name = message['name']
    message_to_client.delay(name, roomstr)


@socketio.on('shorttask', namespace='/test')
def shorttask():

    short_task.apply_async()


@blueprint.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    timezones = pytz.common_timezones

    if request.method == "POST":
        current_user.first_name = request.form.get("first_name")
        current_user.last_name = request.form.get("last_name")

        db.session.commit()

    return render_template(
        "profile.html",
        timezones=timezones,
        segment=get_segment(request)
    )


@blueprint.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    timezones = pytz.common_timezones

    if request.method == "POST":

        latitude_value = request.form.get("latitude")
        longitude_value = request.form.get("longitude")

        app.logger.info(request.form.get("skip_rained_today"))
        app.logger.info(request.form.get("skip_rained_yesterday"))

        if latitude_value is not None and longitude_value is not None and (latitude_value != current_user.latitude or longitude_value != current_user.longitude):

            app.logger.info("Making nominatim request")
            location_info = json.dumps(get_city_country(latitude_value, longitude_value))

            # app.logger.info("Current User City: ", current_user.city)
            # app.logger.info("location_info: ", location_info)

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

        db.session.commit()

    return render_template(
        "settings.html",
        timezones=timezones,
        segment=get_segment(request)
    )


@blueprint.route("/profileimage", methods=['GET', 'POST'])
@login_required
def profileimage():

    app.logger.info(request.files)

    if request.method == 'POST' and 'photo' in request.files:

        try:

            photo_file = request.files['photo']
            photo_file_extension = Path(photo_file.filename).suffix

            photo_filename = str(hashlib.sha1(str(
                current_user.email).encode('utf-8') + str(
                current_user.id).encode('utf-8') + str(
                datetime.datetime.now().timestamp()).encode('utf-8')
                ).hexdigest()) + photo_file_extension

            photos.save(request.files['photo'], name=photo_filename)

            current_user.profileimage = photo_filename
            db.session.commit()

            flash('Profile image updated.')

            return redirect(url_for("home_blueprint.profile"))

        except Exception as e:
            app.logger.info("Exception: ", str(e))

    return redirect(url_for("home_blueprint.profile"))


@blueprint.route("/celery", methods=['GET', 'POST'])
def celery():

    return render_template("celery.html")


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
            return redirect(url_for("home_blueprint.route_default"))

        # Something (user or pass) is not ok
        return render_template(
            "accounts/login.html", msg="Wrong user or password", form=login_form
        )

    if not current_user.is_authenticated:
        return render_template("accounts/login.html", form=login_form)
    return redirect(url_for("home_blueprint.index"))


@blueprint.route("/register", methods=["GET", "POST"])
def register():

    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if "register" in request.form:

        username = request.form["username"]
        email = request.form["email"]

        # Check usename exists
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template(
                "accounts/register.html",
                msg="Username already registered",
                success=False,
                form=create_account_form,
            )

        # Check email exists
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template(
                "accounts/register.html",
                msg="Email already registered",
                success=False,
                form=create_account_form,
            )

        # else we can create the user
        user = User(**request.form)
        db.session.add(user)
        db.session.commit()

        return render_template(
            "accounts/register.html",
            msg='User created please <a href="/login">login</a>',
            success=True,
            form=create_account_form,
        )

    else:
        return render_template("accounts/register.html", form=create_account_form)


@blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home_blueprint.login"))


@blueprint.route("/shutdown")
def shutdown():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Server shutting down..."


## Errors


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
