
import json

from app import app, db
from app.models import Settings
from app.location import get_city_country


def create_or_update_settings_profile(request, name):

    status = None

    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    if latitude is not None and longitude is not None:

        location_info = json.dumps(
            get_city_country(latitude, longitude)
        )

        if "city" in json.loads(location_info)["address"]:

            city = json.loads(location_info)["address"]["city"]
        else:

            city = json.loads(location_info)["address"]["state"]

        country = json.loads(location_info)["address"]["country"]

    is_edit = request.form.get("edit")

    app.logger.info(request.form.get("edit"))

    if is_edit == "True":

        app.logger.info("editing settings profile.")

        settings_profile = Settings.query.filter_by(name=name).first_or_404()

        settings_profile.name = request.form.get("name")
        settings_profile.description = request.form.get("description")

        settings_profile.watering_start_at = request.form.get("water_start_time")
        settings_profile.water_duration_minutes = request.form.get("water_duration_minutes")

        settings_profile.latitude = str(latitude)
        settings_profile.longitude = str(longitude)

        if not ("*" * 16) in request.form.get("apikey"):
            settings_profile.owm_apikey = request.form.get("apikey")

        settings_profile.city = str(city)
        settings_profile.country = str(country)
        settings_profile.timezone = request.form.get("timezone")

        settings_profile.schedule_watering = request.form.get("schedule_watering")

        settings_profile.skip_rained_today = request.form.get("skip_rained_today")
        settings_profile.skip_rained_yesterday = request.form.get("skip_rained_yesterday")
        settings_profile.skip_watered_today = request.form.get("skip_watered_today")
        settings_profile.skip_watered_yesterday = request.form.get("skip_watered_yesterday")

        if not ("*" * 16) in request.form.get("telegram_token"):
            settings_profile.telegram_token = request.form.get("telegram_token")

        settings_profile.telegram_chat_id = request.form.get("telegram_chat_id")

        db.session.commit()

    else:

        app.logger.info("Creating new settings profile.")

        new_settings_profile = Settings(

            name=request.form.get("name"),
            description=request.form.get("description"),

            watering_start_at=request.form.get("water_start_time"),
            water_duration_minutes=request.form.get("water_duration_minutes"),

            latitude=latitude,
            longitude=longitude,
            owm_apikey=request.form.get("apikey"),

            city=city,
            country=country,
            timezone=request.form.get("timezone"),

            schedule_watering=request.form.get("schedule_watering"),

            skip_rained_today=request.form.get("skip_rained_today"),
            skip_rained_yesterday=request.form.get("skip_rained_yesterday"),
            skip_watered_today=request.form.get("skip_watered_today"),
            skip_watered_yesterday=request.form.get("skip_watered_yesterday"),

            telegram_token=request.form.get("telegram_token"),
            telegram_chat_id=request.form.get("telegram_chat_id")
        )

        db.session.add(new_settings_profile)
        db.session.commit()

    return status
