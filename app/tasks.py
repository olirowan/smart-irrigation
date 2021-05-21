import time
from datetime import datetime
import random
from app import app, celery, db
from app.models import Watering
from flask_socketio import SocketIO


@celery.task(
    bind=True,
    base=celery.QueueOnce,
    once={'timeout': 25}
)
def long_task(self):

    message = ''
    total = random.randint(10, 50)
    total = 25
    for i in range(0, 10, 1):
        if not message or i == 9:
            message = 'Watering in progress...'

        self.update_state(
            state='PROGRESS',
            meta={'current': i, 'total': total, 'status': message}
        )

        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@celery.task(
    bind=True,
    base=celery.QueueOnce,
    once={'timeout': 60}
)
def short_task(self):

    socketio = SocketIO(message_queue=app.config['CELERY_BROKER_URL'])

    duration_seconds = 60
    for i in range(0, duration_seconds, 1):
        if i < duration_seconds:
            message = "Watering in progress..."

        socketio.emit("short_response", {
            "current": i,
            "total": duration_seconds,
            "status": message
        }, namespace="/test")

        time.sleep(1)

    water_event = Watering()
    water_event.watered_at = datetime.now().timestamp()
    water_event.water_duration_minutes = (duration_seconds / 60)

    db.session.add(water_event)
    db.session.commit()

    socketio.emit('short_response', {
        "current": 100,
        "total": 100,
        "status": "Done"
        }, namespace='/test')


# message_to_client() function is meant to run as \
# background tasks, so it needs to be decorated with the celery.task decorator
@celery.task(name="task.message")
def message_to_client(name, room):

    socketio = SocketIO(message_queue=app.config['CELERY_BROKER_URL'])
    count = 5
    while count > 1:
        count -= 1

        socketio.emit(
            'response', {'count': count},
            namespace='/test',
            room=room
        )

        time.sleep(1)

    socketio.emit('response', {'name': name}, namespace='/test', room=room)
