FROM python:3.7

WORKDIR /application

COPY ./ ./

ENV TZ=Europe/London

RUN apt-get update && apt-get install -y nginx supervisor
RUN useradd --no-create-home nginx
RUN pip3 install -r requirements.txt
RUN mkdir -p logs

COPY supervisord.conf /etc/
COPY nginx.conf /etc/nginx/
COPY nginx-config.conf /etc/nginx/sites-enabled/default

EXPOSE 80

CMD ["/usr/bin/supervisord"]