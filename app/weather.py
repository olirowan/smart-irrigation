from app.models import Watering
from datetime import datetime, timedelta
from pyowm import OWM
import json
import pytz
from geopy.geocoders import Nominatim
from flask_login import current_user
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

    last_rain_date = None

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

                    if daily_weather.status.lower() == "rain":

                        last_rain_date = convert_local_utc(
                            daily_weather.ref_time
                        )

                        break_parent_loop = True
                        break

    if last_rain_date is None:

        return "a while ago"
    else:
        return datetime.fromtimestamp(last_rain_date)


def get_next_rain_date(location_latitude, location_longitude):

    next_rain_date = None

    upcoming_weather = get_one_call_current(
        location_latitude,
        location_longitude
    )

    current_time = convert_local_utc(datetime.now().timestamp())

    for hourly_weather in upcoming_weather:
        if hourly_weather.status.lower() == "rain":
            if current_time < hourly_weather.ref_time:

                next_rain_date = convert_local_utc(hourly_weather.ref_time)

                break

    if next_rain_date is None:

        return "currently unknown"
    else:
        return datetime.fromtimestamp(next_rain_date)


def get_last_water_date():

    last_water_date = Watering.query.order_by(
        Watering.water_start_time.desc()
    ).first()

    if last_water_date is None:

        return "never", "n/a"
    else:

        last_water_as_date = datetime.fromisoformat(
            str(last_water_date.water_start_time)
        )
        last_water_duration_minutes = last_water_date.water_duration_minutes

        return last_water_as_date, last_water_duration_minutes


def get_next_water_date(location_latitude, location_longitude):

    latest_rain_date = None
    if_rained_today = False
    if_rained_yesterday = False
    if_watered_today = False
    if_watered_yesterday = False
    eod_skip = False

    # Check if user has actually set their preferred watering time
    if (current_user.watering_start_at == "" or current_user.watering_start_at is None):

        return "Configuration Not Set"

    # Get the current datetime to manipulate to match the user settings
    current_utc_timestamp = convert_local_utc(datetime.now().timestamp())
    current_datetime = datetime.fromtimestamp(current_utc_timestamp)

    # Modify the datetimes hour/minute values to match user settings
    modified_datetime = current_datetime.replace(
        hour=int(current_user.watering_start_at.split(":")[0]),
        minute=int(current_user.watering_start_at.split(":")[1]),
        second=0,
        microsecond=0
    )

    # If the hour/minute setting has already passed today, set day to tomorrow
    if modified_datetime > current_datetime:

        next_water_date = modified_datetime
    else:

        next_water_date = modified_datetime + timedelta(days=1)

    # Store the last saved water time
    last_water_date, last_water_duration = get_last_water_date()

    if last_water_date != "never":

        # boolean for whether last watered date was today
        if last_water_date.date() == current_datetime.date():

            if_watered_today = True
            eod_skip = True

        # boolean for whether last watered date was yesterday
        if last_water_date.date() == (current_datetime.date() - timedelta(days=1)):

            if_watered_yesterday = True
            eod_skip = True

    # If user settings are impacted by rainfall:
    #   - store upcoming rain
    #   - store if it rained yesterday
    #   - store if it rained today
    if (current_user.skip_rained_today == "on" or
            current_user.skip_rained_yesterday == "on"):

        upcoming_weather = get_one_call_current(
            location_latitude,
            location_longitude
        )

        for hourly_weather in reversed(upcoming_weather):

            if hourly_weather.status.lower() == "rain":

                latest_rain_date = datetime.fromtimestamp(
                    convert_utc_local(hourly_weather.ref_time)
                )
                break

        if latest_rain_date is None:

            latest_rain_date = "unknown"

        # This will only check todays weather up to the current time,
        # not until the end of the day.
        todays_weather_so_far = get_one_call_history(
            0,
            current_user.latitude,
            current_user.longitude
        )

        yesterdays_weather = get_one_call_history(
            1,
            current_user.latitude,
            current_user.longitude
        )

        for todays_weather_statuses in todays_weather_so_far:

            app.logger.info(todays_weather_statuses)

            if todays_weather_statuses.status.lower() == "rain":

                if_rained_today = True
                eod_skip = True
                break

        if if_rained_today is False:

            forecast_rain = get_next_rain_date(
                current_user.latitude,
                current_user.longitude
            )

            if forecast_rain == "currently unknown":

                if_rained_today = False
                eod_skip = True

            elif forecast_rain.date() <= current_datetime.date():

                if_rained_today = True
                eod_skip = True

        for weather_statuses in yesterdays_weather:

            if weather_statuses.status.lower() == "rain":

                if_rained_yesterday = True
                eod_skip = True
                break

    # If there's no historical watering and the user settings are not
    # impacted by rainfall, then water at next time occurance
    if (last_water_date == "never" and
        ((current_user.skip_rained_today != "on" and current_user.skip_rained_yesterday != "on") or latest_rain_date == "unknown")):

        return next_water_date

    else:

        # Log a bunch of variables for debugging
        app.logger.info("last water date: " + str(last_water_date))

        app.logger.info("if skip rained today: " + str(current_user.skip_rained_today))
        app.logger.info("if skip rained yesterday: " + str(current_user.skip_rained_yesterday))
        app.logger.info("if skip watered today: " + str(current_user.skip_watered_today))
        app.logger.info("if skip watered yesterday: " + str(current_user.skip_watered_yesterday))

        app.logger.info("if watered today: " + str(if_watered_today))
        app.logger.info("if watered yesterday: " + str(if_watered_yesterday))
        app.logger.info("if rained today: " + str(if_rained_today))
        app.logger.info("if rained yesterday: " + str(if_rained_yesterday))

        app.logger.info("latest rain date: " + str(latest_rain_date))


        if current_user.skip_watered_today == "on" and if_watered_today is True:
            if next_water_date.date() <= current_datetime.date():
                next_water_date = next_water_date + timedelta(days=1)

        if current_user.skip_watered_yesterday == "on" and if_watered_yesterday is True:
            if next_water_date.date() <= current_datetime.date():
                next_water_date = next_water_date + timedelta(days=1)

        if current_user.skip_rained_today == "on" and if_rained_today is True:
            if next_water_date.date() <= current_datetime.date():
                next_water_date = next_water_date + timedelta(days=1)

            if next_water_date.date() == latest_rain_date.date():
                next_water_date = next_water_date + timedelta(days=1)

        if current_user.skip_rained_yesterday == "on" and if_rained_yesterday is True:
            if next_water_date.date() <= current_datetime.date():
                next_water_date = next_water_date + timedelta(days=1)

            if next_water_date.date() == (latest_rain_date + timedelta(days=1)).date():
                next_water_date = next_water_date + timedelta(days=1)

        if current_user.schedule_watering == "eod" and eod_skip is True:

            next_water_date = next_water_date + timedelta(days=1)

        return next_water_date
