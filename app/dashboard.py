import pytz
import datetime

from flask_login import current_user

from app import app
from app.models import Settings
from app.weather import get_current_weather, owm_icon_mapping
from app.weather import get_last_rain_date, get_next_rain_date
from app.weather import get_last_water_date, get_next_water_date


def get_dashboard_data():

    if current_user.primary_profile_id is not None:

        # Try and generate dashboard data relevant to the
        # users preferred dashboard.

        settings_profile_data = Settings.query.filter_by(
            id=current_user.primary_profile_id
        ).first()

    elif Settings.query.first() is not None:

        # Otherwise just generate dashboard data for the
        # first settings profile configured in the db.

        settings_profile_data = Settings.query.first()

    else:

        # If there isn't any settings data configured yet
        # then return data to inform user of this.

        dashboard_data = {}

        current_date = datetime.datetime.now(
            pytz.timezone("Europe/London")
        )

        dashboard_data.update(
            {
                "weather_detail": "No Settings Profile Found",
                "weather_icon": "wi wi-na",
                "current_date": current_date,
                "last_rain_date": "API Key Required",
                "next_rain_date": "API Key Required",
                "last_water_date": "N/A",
                "last_water_duration": "N/A",
                "next_water_date": "API Key Required"
            }
        )

        return dashboard_data

    dashboard_data = generate_dashboard_data(settings_profile_data)

    return dashboard_data


def generate_dashboard_data(settings_profile_data_raw):

    dashboard_data = {}
    settings_profile_data = {}

    for column in settings_profile_data_raw.__table__.columns:
        settings_profile_data[column.name] = str(
            getattr(settings_profile_data_raw, column.name)
        )

    current_weather = get_current_weather(
        settings_profile_data
    )

    weather_detail = current_weather.detailed_status

    current_date = datetime.datetime.now(
        pytz.timezone(settings_profile_data["timezone"])
    )

    if current_date.hour >= 6 and current_date.hour <= 20:

        prefix = "wi wi-day-"
    else:
        prefix = "wi wi-night-"

    weather_icon = prefix + owm_icon_mapping(
        current_weather.weather_code
    )

    if weather_icon == "wi wi-night-sunny":
        weather_icon = "wi wi-night-clear"

    last_rain_date = get_last_rain_date(
        settings_profile_data
    )

    next_rain_date = get_next_rain_date(
        settings_profile_data
    )

    last_water_date, last_water_duration = get_last_water_date()

    next_water_date = get_next_water_date(
        settings_profile_data
    )

    dashboard_data.update(
        {
            "weather_detail": weather_detail,
            "weather_icon": weather_icon,
            "city": settings_profile_data["city"],
            "current_date": current_date,
            "last_rain_date": last_rain_date,
            "next_rain_date": next_rain_date,
            "last_water_date": last_water_date,
            "last_water_duration": last_water_duration,
            "next_water_date": next_water_date
        }
    )

    app.logger.info(dashboard_data)

    return dashboard_data
