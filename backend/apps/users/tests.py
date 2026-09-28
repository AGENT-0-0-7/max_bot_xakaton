import json
import urllib.parse
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.test import SimpleTestCase, override_settings

from apps.users.auth_utils import generate_jwt_for_user, validate_max_init_data


class MaxInitDataAuthTests(SimpleTestCase):
    @override_settings(MAX_DEMO_MODE=True)
    def test_mock_init_data_is_valid(self):
        payload = {
            "id": 1001,
            "first_name": "Alice",
            "last_name": "Example",
            "username": "alice_example",
        }
        init_data = (
            "user="
            + urllib.parse.quote(json.dumps(payload))
            + "&hash=mock_hash"
        )

        result = validate_max_init_data(init_data)

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1001)
        self.assertEqual(result["username"], "alice_example")

    @override_settings(MAX_DEMO_MODE=False)
    def test_mock_init_data_is_rejected_outside_demo_mode(self):
        result = validate_max_init_data(
            "user=%7B%22id%22%3A1001%7D&hash=mock_hash"
        )
        self.assertIsNone(result)

    @override_settings(MAX_DEMO_MODE=False, MAX_BOT_TOKEN="test-token")
    def test_fresh_signed_max_init_data_is_valid(self):
        payload = {
            "id": 1002,
            "first_name": "Max",
            "username": "max_user",
        }
        data = {
            "auth_date": str(
                int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp())
            ),
            "user": json.dumps(payload, separators=(",", ":")),
        }
        launch_params = "\n".join(
            "{}={}".format(key, data[key]) for key in sorted(data)
        )
        import hashlib
        import hmac

        secret = hmac.new(
            b"WebAppData", b"test-token", hashlib.sha256
        ).digest()
        data["hash"] = hmac.new(
            secret, launch_params.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        result = validate_max_init_data(urllib.parse.urlencode(data))

        self.assertEqual(result["id"], 1002)

    def test_database_configuration_is_available(self):
        self.assertIn("default", settings.DATABASES)

    def test_jwt_can_be_generated_and_decoded(self):
        class FakeUser:
            id = 42
            max_id = 777
            username = "demo_user"

        token = generate_jwt_for_user(FakeUser())

        self.assertTrue(token)
        self.assertIn(".", token)
        self.assertIn(
            "user_id",
            __import__("jwt").decode(
                token, settings.SECRET_KEY, algorithms=["HS256"]
            ),
        )
