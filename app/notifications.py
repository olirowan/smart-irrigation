import urllib
import requests
from app import app


def telegram_notify(notification, settings_profile_data):

    app.logger.info("Posting message to telegram")

    telegram_api_endpoint = \
        'https://api.telegram.org/bot%s/sendMessage?chat_id=%s&text=%s' % (
                settings_profile_data.telegram_token,
                settings_profile_data.telegram_chat_id,
                urllib.parse.quote_plus(str(notification))
        )

    response = requests.get(telegram_api_endpoint, timeout=10)
    app.logger.info(response.text)
