import os
import hashlib
import binascii
from app import celery


def get_celery_worker_status():

    inspection = celery.control.inspect()

    availability = inspection.ping()
    stats = inspection.stats()
    registered_tasks = inspection.registered()
    active_tasks = inspection.active()
    scheduled_tasks = inspection.scheduled()

    result = {
        'availability': availability,
        'stats': stats,
        'registered_tasks': registered_tasks,
        'active_tasks': active_tasks,
        'scheduled_tasks': scheduled_tasks
    }

    return result


def hash_pass(password):

    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')

    pwdhash = hashlib.pbkdf2_hmac(
        'sha512',
        password.encode('utf-8'),
        salt, 100000
    )

    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash)


def verify_pass(provided_password, stored_password):

    stored_password = stored_password.decode('ascii')
    salt = stored_password[:64]
    stored_password = stored_password[64:]

    pwdhash = hashlib.pbkdf2_hmac(
        'sha512',
        provided_password.encode('utf-8'),
        salt.encode('ascii'),
        100000
    )

    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password
