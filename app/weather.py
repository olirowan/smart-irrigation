from datetime import datetime, timedelta, timezone
from pyowm import OWM
import json
import os
from geopy.geocoders import Nominatim
from app import app
from flask_login import current_user


def init_owm():

    owm = OWM(current_user.owm_apikey)
    mgr = owm.weather_manager()

    return mgr


# location_latitude = 52.9212096
# location_longitude = -1.542163

# https://nominatim.openstreetmap.org/reverse?lat=52.9212096&lon=-1.542163&format=json&addressdetails=1


def get_city_country(latitude, longitude):

    geolocator = Nominatim(user_agent="SmartIrrigation", scheme='https')

    lat_long = "% s, % s" % (str(latitude), str(longitude))
    location = geolocator.reverse(lat_long, timeout=3)

    return location.raw


def get_previous_day_timestamp(day_count):

    return int(
        (datetime.now() - timedelta(days=day_count))
        .replace(tzinfo=timezone.utc).timestamp()
    )


def get_one_call_history(day_count, location_latitude, location_longitude):

    timestamp = get_previous_day_timestamp(day_count)

    mgr = init_owm()

    weather = mgr.one_call_history(
        lat=location_latitude,
        lon=location_longitude,
        dt=timestamp
    )

    return weather.forecast_hourly


def owm_icon_mapping(weather_code):

    app.logger.info(os.getcwd())

    with open('iconmapping.json') as f:
        icon_mapping_data = json.load(f)

        weather_icon = icon_mapping_data[str(weather_code)]["icon"]

    return weather_icon


def get_one_call_current(location_latitude, location_longitude):

    mgr = init_owm()

    weather = mgr.one_call(
        lat=location_latitude,
        lon=location_longitude,
    )

    return weather


def get_current_weather(city, country):

    mgr = init_owm()

    observation = mgr.weather_at_place(city + "," + country)

    return observation.weather
