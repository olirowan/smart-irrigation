import time
import datetime

from flask_socketio import SocketIO

from app import app, celery, db, task_schedule
from app.models import Settings, Watering
from app.notifications import telegram_notify
from app.weather import get_next_water_date


# Check through settings profiles to water at defined times.
@task_schedule.scheduled_job('cron', minute='*')
def check_water_routine():

    app.logger.info("Checking Watering Schedule")

    current_hour_minute = (
        datetime.datetime.now()
    ).strftime("%R")

    with app.app_context():

        settings_profiles = Settings.query.all()

    for settings_profile in settings_profiles:

        app.logger.info(
            "Settings Profile found for: " +
            str(settings_profile.name)
        )

        if settings_profile.watering_start_at == str(current_hour_minute):

            app.logger.info(
                "Settings Profile: " +
                str(settings_profile.name) +
                " is scheduled to water at this time."
            )

            settings_profile_data = {}

            for column in settings_profile.__table__.columns:
                settings_profile_data[column.name] = str(
                    getattr(
                        settings_profile,
                        column.name
                    )
                )

            next_water_date = get_next_water_date(
                settings_profile_data
            )

            app.logger.info(next_water_date.strftime("%Y-%m-%d %k:%m"))
            app.logger.info(datetime.datetime.now().strftime("%Y-%m-%d %k:%m"))

            if (next_water_date.strftime("%Y-%m-%d %k:%m") ==
                    datetime.datetime.now().strftime("%Y-%m-%d %k:%m")):

                duration_seconds = int(
                    settings_profile_data["water_duration_minutes"]
                ) * 60

                water_plants.delay(settings_profile_data, duration_seconds, 1)

            else:

                app.logger.info(
                    "Settings Profile: " +
                    str(settings_profile.name) +
                    " is configured to skip this watering."
                )

        else:

            app.logger.info(
                "Settings Profile: " +
                str(settings_profile.name) +
                " is not scheduled to water at this time."
            )


@celery.task(
    base=celery.QueueOnce,
    once={'timeout': 60 * 60}
)
def water_plants(settings_profile_data, duration_seconds, is_adhoc_request):

    rain = u'\U00002614'

    socketio = SocketIO(message_queue=app.config['CELERY_BROKER_URL'])

    start_time = datetime.datetime.now()

    if app.config['DEMO_MODE'] == "False":

            import RPi.GPIO as GPIO

            telegram_notify(
                rain + " - Scheduled watering has started at: " +
                str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"))
            )

            GPIO.setmode(GPIO.BCM)
            GPIO_PIN = 21

            GPIO.setup(GPIO_PIN, GPIO.OUT)
            GPIO.output(GPIO_PIN, False)

            GPIO.output(GPIO_PIN, True)

    else:

        app.logger.info(
            "DEMO MODE ENABLED for Settings Profile: " +
            settings_profile_data["name"] +
            " has started watering."
        )

    for i in range(0, duration_seconds, 1):

        if i < duration_seconds:

            message = "Watering in progress..."

        socketio.emit("short_response", {
            "current": i,
            "total": duration_seconds,
            "status": message
        }, namespace="/water")

        time.sleep(1)

    new_water_event = Watering(
        water_start_time=start_time,
        water_end_time=datetime.datetime.now(),
        adhoc_request=is_adhoc_request,
        status="completed",
        water_duration_minutes=int((duration_seconds / 60))
    )

    db.session.add(new_water_event)
    db.session.commit()

    if app.config['DEMO_MODE'] == "False":

        GPIO.output(GPIO_PIN, False)
        telegram_notify(
            rain + " - Scheduled watering has completed at: " +
            str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"))
        )
        GPIO.cleanup()

    else:

        app.logger.info(
            "DEMO MODE ENABLED for Settings Profile: " +
            settings_profile_data["name"] +
            " has completed watering."
        )

    socketio.emit('short_response', {
        "current": 100,
        "total": 100,
        "status": "Done"
        }, namespace='/water')


@celery.task(
    base=celery.QueueOnce,
    once={'timeout': 60}
)
def cancel_water_plants():

    app.logger.info("Cancelling any watering in progress.")

    socketio = SocketIO(message_queue=app.config['CELERY_BROKER_URL'])

    if app.config['DEMO_MODE'] == "False":

        import RPi.GPIO as GPIO

        telegram_notify(
            "Cancelling any in progress watering at: " +
            str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"))
        )

        GPIO.setmode(GPIO.BCM)
        GPIO_PIN = 21

        GPIO.setup(GPIO_PIN, GPIO.OUT)
        GPIO.output(GPIO_PIN, False)
        GPIO.cleanup()

    socketio.emit('short_response', {
        "current": 100,
        "total": 100,
        "status": "Done"
        }, namespace='/water')
