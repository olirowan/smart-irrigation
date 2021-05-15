import time
import random
from app import app, celery
from flask_socketio import SocketIO, emit, join_room


# def make_celery(app):

#     celery = Celery(
#         app.import_name,
#         backend=app.config['CELERY_RESULT_BACKEND'],
#         broker=app.config['CELERY_BROKER_URL']
#     )
#     celery.conf.update(app.config)

#     celery.conf.ONCE = {
#         'backend': 'celery_once.backends.Redis',
#         'settings': {
#             'url': app.config['CELERY_BROKER_URL'],
#             'default_timeout': 60 * 60
#         }
#     }

#     class ContextTask(celery.Task):
#         def __call__(self, *args, **kwargs):
#             with app.app_context():
#                 return self.run(*args, **kwargs)

#     celery.Task = ContextTask

#     class ContextQueueOnce(QueueOnce):
#         def __call__(self, *args, **kwargs):
#             with app.app_context():
#                 return super(ContextQueueOnce, self).__call__(*args, **kwargs)

#     celery.QueueOnce = ContextQueueOnce

#     return celery


# celery = make_celery(app)


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

        self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'status': message})

        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@celery.task(
    bind=True,
    base=celery.QueueOnce,
    once={'timeout': 8}
)
def short_task(self):

    socketio = SocketIO(message_queue=app.config['CELERY_BROKER_URL'])

    total = 8
    for i in range(0, total, 1):
        if i < total:
            message = "Watering in progress..."

        socketio.emit("short_response", {
            "current": i,
            "total": total,
            "status": message
        }, namespace="/test")

        time.sleep(1)

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
        socketio.emit('response', {'count': count}, namespace='/test', room=room)
        time.sleep(1)
    socketio.emit('response', {'name': name}, namespace='/test', room=room)
