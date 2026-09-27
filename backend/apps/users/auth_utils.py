import hmac
import hashlib
import json
import urllib.parse
from django.conf import settings
from django.contrib.auth import get_user_model
import jwt
from datetime import datetime, timedelta

User = get_user_model()

def validate_max_init_data(init_data_raw: str) -> dict | None:
    """
    Validates initData string received from MAX Bridge using HMAC-SHA256 with MAX_BOT_TOKEN.
    Returns user payload dict if valid, or None if invalid.
    Supports mock/testing bypass if MAX_BOT_TOKEN is 'mock_token' or init_data_raw contains 'mock_hash'.
    """
    if not init_data_raw:
        return None

    try:
        parsed_data = urllib.parse.parse_qs(init_data_raw, keep_blank_values=True)
        # Flatten dictionary values
        data_dict = {k: v[0] for k, v in parsed_data.items()}
    except Exception:
        return None

    # Handle mock / test environment validation
    if settings.MAX_BOT_TOKEN == 'mock_token' or data_dict.get('hash') == 'mock_hash':
        user_str = data_dict.get('user', '{}')
        try:
            user_data = json.loads(user_str)
            return user_data
        except Exception:
            return None

    received_hash = data_dict.pop('hash', None)
    if not received_hash:
        return None

    # Build data check string according to Telegram/MAX initData validation standard
    data_check_arr = []
    for key in sorted(data_dict.keys()):
        data_check_arr.append(f"{key}={data_dict[key]}")
    data_check_string = "\n".join(data_check_arr)

    # Calculate HMAC-SHA256
    secret_key = hmac.new(b"WebAppData", settings.MAX_BOT_TOKEN.encode('utf-8'), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()

    if hmac.compare_digest(calculated_hash, received_hash):
        user_str = data_dict.get('user', '{}')
        try:
            return json.loads(user_str)
        except Exception:
            return None

    return None


def generate_jwt_for_user(user) -> str:
    payload = {
        'user_id': user.id,
        'max_id': user.max_id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


def decode_jwt_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
