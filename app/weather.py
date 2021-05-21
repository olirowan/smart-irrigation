from app.models import Watering
from datetime import datetime, timedelta
from pyowm import OWM
import json
import pytz
from geopy.geocoders import Nominatim
from flask_login import current_user
from app.models import Watering
from app import app


def init_owm():

    owm = OWM(current_user.owm_apikey)
    mgr = owm.weather_manager()

    return mgr


def get_city_country(latitude, longitude):

    geolocator = Nominatim(user_agent="SmartIrrigation", scheme='https')

    lat_long = "% s, % s" % (str(latitude), str(longitude))
    location = geolocator.reverse(lat_long, timeout=3)

    return location.raw


def get_previous_day_timestamp(day_count):

    current_time = convert_local_utc(datetime.now().timestamp())

    return int(
        (datetime.fromtimestamp(
            current_time) - timedelta(days=day_count)).timestamp()
    )


def convert_local_utc(timestamp):

    user_timezone = pytz.timezone(current_user.timezone)

    toconvert_timestamp = datetime.fromtimestamp(timestamp)

    converted_timestamp = user_timezone.normalize(
        user_timezone.localize(toconvert_timestamp)
    ).astimezone(pytz.utc)

    return converted_timestamp.timestamp()


def convert_utc_local(timestamp):

    user_timezone = pytz.timezone(current_user.timezone)

    toconvert_timestamp = datetime.fromtimestamp(timestamp)

    converted_timestamp = pytz.utc.localize(
        toconvert_timestamp,
        is_dst=None
    ).astimezone(user_timezone)

    return converted_timestamp.timestamp()


def get_one_call_history(day_count, location_latitude, location_longitude):

    timestamp = get_previous_day_timestamp(day_count)

    mgr = init_owm()

    weather = mgr.one_call_history(
        dt=timestamp,
        lat=float(location_latitude),
        lon=float(location_longitude)
    )

    return weather.forecast_hourly


def owm_icon_mapping(weather_code):

    with open('iconmapping.json') as f:
        icon_mapping_data = json.load(f)

        weather_icon = icon_mapping_data[str(weather_code)]["icon"]

    return weather_icon


def get_one_call_current(location_latitude, location_longitude):

    mgr = init_owm()

    weather = mgr.one_call(
        lat=float(location_latitude),
        lon=float(location_longitude),
    )

    return weather.forecast_hourly


def get_current_weather(city, country):

    mgr = init_owm()

    observation = mgr.weather_at_place(city + "," + country)

    return observation.weather


def get_last_rain_date(location_latitude, location_longitude):

    current_weather = get_current_weather(
        current_user.city,
        current_user.country
    )

    if current_weather.status.lower() == "rain":

        current_time = convert_local_utc(datetime.now().timestamp())

        return datetime.fromtimestamp(current_time)

    else:

        break_parent_loop = False

        for days_ago in range(0, 6):

            if break_parent_loop is True:

                break
            else:

                historical_weather = get_one_call_history(
                    days_ago,
                    location_latitude,
                    location_longitude
                )

                for daily_weather in reversed(historical_weather):

                    app.logger.info(daily_weather)

                    if daily_weather.status.lower() == "rain":

                        last_rain_date = convert_local_utc(
                            daily_weather.ref_time
                        )

                        break_parent_loop = True
                        break

    if last_rain_date is None:

        return "currently unknown"
    else:
        return datetime.fromtimestamp(last_rain_date)


def get_next_rain_date(location_latitude, location_longitude):

    upcoming_weather = get_one_call_current(
        location_latitude,
        location_longitude
    )

    for hourly_weather in upcoming_weather:

        if hourly_weather.status == "Rain":

            next_rain_date = convert_local_utc(hourly_weather.ref_time)

            break

    if next_rain_date is None:

        return "currently unknown"
    else:
        return datetime.fromtimestamp(next_rain_date)


def get_last_water_date():

    last_water_date = Watering.query.order_by(
        Watering.watered_at.desc()
    ).first()

    if last_water_date is None:

        return "never"
    else:
        return datetime.fromtimestamp(float(last_water_date.watered_at))


def get_next_water_date(location_latitude, location_longitude):

    upcoming_weather = get_one_call_current(
        location_latitude,
        location_longitude
    )

    next_water_date = "Unknown"

    for hourly_weather in reversed(upcoming_weather):

        if hourly_weather.status == "Rain":

            next_water_date = convert_utc_local(hourly_weather.ref_time)

            break

    if next_water_date is None:

        return "currently unknown"
    else:
        return datetime.fromtimestamp(next_water_date)
