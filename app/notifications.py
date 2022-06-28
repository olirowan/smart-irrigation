import urllib
import requests
from app import app


def telegram_notify(notification):

    telegram_token = str(app.config["TELEGRAM_TOKEN"])
    telegram_chat_id = str(app.config["TELEGRAM_CHAT_ID"])

    if telegram_token is not None and telegram_chat_id is not None:

        app.logger.info("Posting message to telegram")

        telegram_api_endpoint = \
            'https://api.telegram.org/bot%s/sendMessage?chat_id=%s&text=%s' % (
                    telegram_token,
                    telegram_chat_id,
                    urllib.parse.quote_plus(str(notification))
            )

        response = requests.get(telegram_api_endpoint, timeout=10)
        app.logger.info(response.text)

    else:

        app.logger.warning("Failed to send telegram notification.")

