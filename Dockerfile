FROM python:3.7
WORKDIR /application
COPY ./ ./
RUN apt-get update && apt-get install -y nginx
RUN pip3 install -r requirements.txt
RUN mkdir -p app/logs
COPY wsgi.ini /etc/uwsgi/wsgi.ini
COPY nginx-config.conf /etc/nginx/sites-enabled/application.conf
RUN service nginx reload
EXPOSE 80
ENTRYPOINT [ "./gunicorn.sh" ]

# docker run --name server1 -it -e SESSION_TYPE=redis -e SESSION_REDIS=redis://192.168.1.121:6379/0 -e CELERY_RESULT_BACKEND=redis://192.168.1.121:6379/0 -e CELERY_BROKER_URL=redis://192.168.1.121:6379/0 -e SQLALCHEMY_DATABASE_URI=mysql://smartirrigation:changeme@192.168.1.121:3306/smartirrigation -p 8000:8000 olirowan/smart-irrigation:v0.1

# -e CELERY_RESULT_BACKEND=redis://192.168.1.121:6379/0
# -e CELERY_BROKER_URL=redis://192.168.1.121:6379/0
# -e SQLALCHEMY_DATABASE_URI=mysql://smartirrigation:changeme@192.168.1.121:3306/smartirrigation
# -e SESSION_TYPE=redis
# -e SESSION_REDIS=redis://192.168.1.121:6379/0