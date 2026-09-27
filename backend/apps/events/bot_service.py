import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_max_bot_message(max_id: int, text: str) -> bool:
    """
    Sends notification message to user via MAX Bot API.
    If bot API endpoint or token is mock, logs and returns True.
    """
    if not max_id:
        return False

    bot_token = getattr(settings, 'MAX_BOT_TOKEN', None)
    bot_api_url = getattr(settings, 'MAX_BOT_API_URL', 'https://api.max.ru/bot')

    if not bot_token or bot_token == 'mock_token':
        logger.info(f"[MOCK MAX BOT MSG] To max_id={max_id}: {text}")
        return True

    url = f"{bot_api_url.rstrip('/')}/sendMessage"
    payload = {
        'chat_id': max_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    headers = {
        'Authorization': f"Bearer {bot_token}",
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            logger.info(f"Successfully sent MAX message to {max_id}")
            return True
        else:
            logger.warning(f"Failed to send MAX message to {max_id}: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending MAX bot message: {e}")
        return False
