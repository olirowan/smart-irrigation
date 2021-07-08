import time
import datetime
from app import app, celery, db, task_schedule
from app.models import User, Watering
from app.weather import get_next_water_date
from app.util import telegram_notify
from flask_socketio import SocketIO


# Write a task that checks the next_water_date at the user specified time.
# If the time matches up, then execute the default watering.
@task_schedule.scheduled_job('cron', minute='*')
def check_water_routine():

    with app.app_context():
     
        scheduled_user = db.session.query(User).one_or_none()

    if scheduled_user is not None:

        current_hour_minute = (
            datetime.datetime.now() + 
            datetime.timedelta(minutes=1)
        ).strftime("%R")

        if scheduled_user.watering_start_at == str(current_hour_minute):

            next_water_date = get_next_water_date(
                scheduled_user.latitude,
                scheduled_user.longitude,
                scheduled_user
            )

            if (next_water_date.strftime("%Y-%m-%d %k:%m") == 
                (datetime.datetime.now() -
                datetime.timedelta(minutes=1))
                .strftime("%Y-%m-%d %k:%m")):

                app.logger.info("Starting Scheduled Watering.")

                time_seconds = int(scheduled_user.water_duration_minutes) * 60
                water_plants.delay(time_seconds, 1)

            else:

                app.logger.info("Scheduled time matched, but not watering now.")
        else:

            app.logger.info("Nope, not this minute.")
    
    else:

        app.logger.info("No user found.")


@celery.task(
    base=celery.QueueOnce,
    once={'timeout': 60 * 60}
)
def water_plants(duration_seconds, is_adhoc_request):

    app.logger.info("Watering for: " + str(duration_seconds) + " seconds.")

    socketio = SocketIO(message_queue=app.config['CELERY_BROKER_URL'])

    start_time = datetime.datetime.now()

    if app.config['DEMO_MODE'] is False:

        import RPi.GPIO as GPIO

        telegram_notify("Scheduled watering has started at: " + str(start_time))

        GPIO.setmode(GPIO.BCM)
        GPIO_PIN = 21

        GPIO.setup(GPIO_PIN, GPIO.OUT)
        GPIO.output(GPIO_PIN, False)

        GPIO.output(GPIO_PIN, True)

    for i in range(0, duration_seconds, 1):

        if i < duration_seconds:

            message = "Watering in progress..."

        socketio.emit("short_response", {
            "current": i,
            "total": duration_seconds,
            "status": message
        }, namespace="/water")

        time.sleep(1)

    water_event = Watering()
    water_event.water_start_time = start_time
    water_event.water_end_time = datetime.datetime.now()
    water_event.adhoc_request = is_adhoc_request
    water_event.status = "completed"
    water_event.water_duration_minutes = int((duration_seconds / 60))

    db.session.add(water_event)
    db.session.commit()

    if app.config['DEMO_MODE'] is False:

        GPIO.output(GPIO_PIN, False)
        telegram_notify("Scheduled watering has completed at: " + str(datetime.datetime.now()))
        GPIO.cleanup()

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

    start_time = datetime.datetime.now()

    if app.config['DEMO_MODE'] is False:

        import RPi.GPIO as GPIO

        telegram_notify("Cancelling any in progress watering at: " + str(start_time))

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