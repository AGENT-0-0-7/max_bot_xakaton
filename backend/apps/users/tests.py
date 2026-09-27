import json
import urllib.parse

from django.conf import settings
from django.test import SimpleTestCase

from apps.users.auth_utils import generate_jwt_for_user, validate_max_init_data


class MaxInitDataAuthTests(SimpleTestCase):
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

    def test_docker_profile_defaults_to_postgres_when_credentials_exist(self):
        self.assertFalse(getattr(settings, "USE_SQLITE", True))

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
