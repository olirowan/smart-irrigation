import time
from datetime import datetime
from app import app, celery, db
from app.models import Watering
from flask_socketio import SocketIO


@celery.task(
    base=celery.QueueOnce,
    once={'timeout': 60 * 60}
)
def water_plants(duration_seconds, is_adhoc_request):

    app.logger.info("Watering for: " + str(duration_seconds) + " seconds.")

    socketio = SocketIO(message_queue=app.config['CELERY_BROKER_URL'])

    start_time = datetime.now()

    if app.config['DEMO_MODE'] is False:

        import RPi.GPIO as GPIO

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
    water_event.water_end_time = datetime.now()
    water_event.adhoc_request = is_adhoc_request
    water_event.status = "completed"
    water_event.water_duration_minutes = int((duration_seconds / 60))

    db.session.add(water_event)
    db.session.commit()

    if app.config['DEMO_MODE'] is False:

        GPIO.output(GPIO_PIN, False)
        GPIO.cleanup()

    socketio.emit('short_response', {
        "current": 100,
        "total": 100,
        "status": "Done"
        }, namespace='/water')
