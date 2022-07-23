# smart-irrigation

Source code for the smart-irrigation flask project that waters plants.

 - Running locally:

```bash

. ./set_env.sh
source venv/bin/activate
python smart-irrigation.py 
```

# Smart Irrigaton

`Smart Irrigaton` is an application inspired by the idea of watering garden plants using a Raspberry Pi:

This repo contains the software that complements the hardware side of the project - which controls the water release via GPIO Pins and a Solenoid Valve.

The design is 

## Getting Started

Clone this repository, install dependencies, and set environment variables:

```bash
$ git clone https://github.com/olirowan/smart-irrigation.git
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ cp .example.env .env
```

Modify the _.env_ to set the following values:

- __DEMO_MODE__ - If True, this won't attempt any GPIO connections but will simulate watering time/responses in the frontend.
- __SQLALCHEMY_DATABASE_URI__ - Specify a database endpoint (optional, default: SQLite3 file)
- __SESSION_TYPE__ - Sessions can be managed with _redis_ or _filesystem_ (optional, default: filesystem)
- __SESSION_REDIS__ - If _redis_ is set as the __SESSION_TYPE__ then you must provide a redis endpoint.
- __CELERY_BROKER_URL__ - Specify a redis endpoint for the task queue (required)
- __CELERY_RESULT_BACKEND__ - Specify a redis endpoint for the task queue (required)


Configure the database:

```bash
$ flask db upgrade
```

## Running Locally

Run the application from the command line as follows:

```bash
$ flask run
```

Along with running the application, you must also run a Celery worker.

```bash
$ ./venv/bin/celery -A app.celery worker -B
```

Optionally you can separate workers to run Celery Beat independently.

```bash
$ ./venv/bin/celery -A app.celery worker
$ ./venv/bin/celery -A app.celery beat
```

## Running in Production

The Celery worker(s) should be running on the RPi connected to the Solenoid Valve.

The frontend can be run on the RPi or it can be hosted elsewhere, as long as both the frontend and Celery worker are able to connect to the same redis and database endpoints.

Due to this, I recommend running the frontend in a container for quick setup.
If you don't wish to use containers then the configuration from _supervisord.conf_ and _nginx-config.conf_ can be used as a reference.

## Build in Docker

This will create a container running the frontend application however you will still need celery workers running.

```
docker build -t olirowan/smart-irrigation:v1.0 .

docker run --name smartirrigation -it \
    -e DEMO_MODE=True
    -e SESSION_TYPE=redis \
    -e SESSION_REDIS=redis://redis-host:6379/0 \
    -e CELERY_RESULT_BACKEND=redis://redis-host:6379/1 \
    -e CELERY_BROKER_URL=redis://redis-host:6379/1 \
    -e SQLALCHEMY_DATABASE_URI=mysql://demo:demo@db-host:3306/smartirrigation \
    -p 5000:80 -\
    olirowan/smart-irrigation:v0.1
```



## Configure Application

You should now be able to access the frontend at http://127.0.0.1:5000/
From here the dashboard should prompt you to create a _Settings Profile_ (_Settings_ > _Add New Settings Profile_)

This will require an OpenWeatherMap API Key which can be obtained from signing up to their platform:

- https://openweathermap.org/api


## Further Information

Additional details (including a hardware build) about this project can be found onwards from this blogpost:

- https://blog.olirowan.com/raspberry-pi-home-irrigation-part-1-overview/