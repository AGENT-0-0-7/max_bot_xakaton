import hashlib
import hmac
import json
import urllib.parse
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings

def validate_max_init_data(init_data_raw: str) -> dict | None:
    """
    Validate MAX WebAppData with the official HMAC-SHA256 algorithm.

    A deliberately marked mock payload is accepted only in demo mode, allowing
    the Docker demo to run without a real MAX bot token.
    """
    if not init_data_raw:
        return None

    try:
        pairs = urllib.parse.parse_qsl(
            init_data_raw, keep_blank_values=True, strict_parsing=True
        )
    except Exception:
        return None

    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)) or keys.count("hash") != 1:
        return None
    data_dict = dict(pairs)

    if settings.MAX_DEMO_MODE and data_dict.get("hash") == "mock_hash":
        user_str = data_dict.get("user", "{}")
        try:
            user_data = json.loads(user_str)
            return user_data if user_data.get("id") else None
        except Exception:
            return None

    if not settings.MAX_BOT_TOKEN:
        return None

    received_hash = data_dict.pop("hash")
    auth_date = data_dict.get("auth_date")
    try:
        is_fresh = (
            abs(datetime.now(timezone.utc).timestamp() - int(auth_date))
            <= 60 * 60
        )
    except (TypeError, ValueError):
        is_fresh = False
    if not is_fresh:
        return None

    launch_params = "\n".join(
        "{}={}".format(key, data_dict[key]) for key in sorted(data_dict)
    )
    secret_key = hmac.new(
        b"WebAppData",
        settings.MAX_BOT_TOKEN.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        secret_key, launch_params.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(calculated_hash, received_hash):
        user_str = data_dict.get("user", "{}")
        try:
            user_data = json.loads(user_str)
            return user_data if user_data.get("id") else None
        except Exception:
            return None

    return None


def generate_jwt_for_user(user) -> str:
    payload = {
        "user_id": user.id,
        "max_id": user.max_id,
        "username": user.username,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


def decode_jwt_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
