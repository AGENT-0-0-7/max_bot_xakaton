import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def send_max_bot_message(max_id: int, text: str) -> bool:
    """
    Send a notification through the official MAX Bot API.

    Demo mode never sends an external request and logs the notification instead.
    """
    if not max_id:
        return False

    if settings.MAX_DEMO_MODE:
        logger.info("[DEMO MAX BOT] To max_id=%s: %s", max_id, text)
        return True

    if not settings.MAX_BOT_TOKEN:
        logger.warning("MAX notification skipped: token is absent")
        return False

    url = "{}/messages".format(settings.MAX_BOT_API_URL)
    headers = {
        "Authorization": settings.MAX_BOT_TOKEN,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            params={"user_id": max_id},
            json={"text": text, "format": "markdown"},
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as error:
        logger.error("Error sending MAX bot message: %s", error)
        return False
