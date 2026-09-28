from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.events.models import Event, EventCategory, EventStatus, Registration

User = get_user_model()


class EventApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="participant",
            password="pass",
            first_name="Participant",
            max_id=101,
        )
        self.organizer = User.objects.create_user(
            username="organizer",
            password="pass",
            first_name="Organizer",
            max_id=102,
        )
        self.event = Event.objects.create(
            organizer=self.organizer,
            title="Test event",
            description="A real test event",
            category=EventCategory.CULTURE,
            address="Tyumen",
            latitude=57.153,
            longitude=65.534,
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=2),
            max_participants=1,
            status=EventStatus.APPROVED,
        )

    def test_event_list_is_nearby_and_public(self):
        response = self.client.get(
            "/api/v1/events/?lat=57.153033&lon=65.534328&radius_km=5"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], self.event.id)
        self.assertIn("distance_meters", response.data[0])

    def test_register_is_idempotent_and_can_be_cancelled(self):
        self.client.force_authenticate(self.user)

        first = self.client.post("/api/v1/events/{}/register/".format(self.event.id))
        second = self.client.post("/api/v1/events/{}/register/".format(self.event.id))
        cancelled = self.client.delete(
            "/api/v1/events/{}/registration/".format(self.event.id)
        )

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertFalse(first.data["notification_sent"])
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data["message"], "You are already registered")
        self.assertEqual(cancelled.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Registration.objects.filter(user=self.user, event=self.event).exists()
        )

    def test_full_event_does_not_create_a_second_registration(self):
        another_user = User.objects.create_user(
            username="another",
            password="pass",
            first_name="Another",
            max_id=103,
        )
        Registration.objects.create(user=another_user, event=self.event)
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/v1/events/{}/register/".format(self.event.id)
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            Registration.objects.filter(user=self.user, event=self.event).exists()
        )

    def test_organizer_event_is_created_for_moderation(self):
        self.client.force_authenticate(self.organizer)
        response = self.client.post(
            "/api/v1/events/",
            {
                "title": "New event",
                "description": "Submitted by organizer",
                "category": EventCategory.SPORT,
                "address": "Sports venue",
                "latitude": 57.15,
                "longitude": 65.53,
                "start_time": (timezone.now() + timedelta(days=3)).isoformat(),
                "end_time": (timezone.now() + timedelta(days=3, hours=2)).isoformat(),
                "max_participants": 20,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], EventStatus.PENDING)
        self.assertEqual(
            Event.objects.get(pk=response.data["id"]).organizer, self.organizer
        )

    def test_invalid_schedule_is_rejected(self):
        self.client.force_authenticate(self.organizer)
        response = self.client.post(
            "/api/v1/events/",
            {
                "title": "Invalid event",
                "description": "End precedes start",
                "category": EventCategory.SPORT,
                "address": "Sports venue",
                "latitude": 57.15,
                "longitude": 65.53,
                "start_time": (timezone.now() + timedelta(days=3)).isoformat(),
                "end_time": (timezone.now() + timedelta(days=2)).isoformat(),
                "max_participants": 20,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_time", response.data)

    def test_webhook_checks_official_max_secret_header(self):
        body = {"update_type": "message_created"}
        with override_settings(MAX_WEBHOOK_SECRET="secret_12345"):
            denied = self.client.post("/webhooks/max/", body, format="json")
            accepted = self.client.post(
                "/webhooks/max/",
                body,
                format="json",
                HTTP_X_MAX_BOT_API_SECRET="secret_12345",
            )

        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(accepted.status_code, status.HTTP_200_OK)

    @override_settings(
        MAX_DEMO_MODE=False,
        MAX_BOT_TOKEN="test-token",
        MAX_BOT_API_URL="https://platform-api2.max.ru",
        MAX_WEBHOOK_URL="https://events.example.com/webhooks/max/",
        MAX_WEBHOOK_SECRET="webhook_secret_123",
    )
    @patch("apps.events.management.commands.setup_max_webhook.requests.post")
    def test_webhook_setup_uses_official_subscription_contract(self, post):
        response = Mock()
        response.json.return_value = {"success": True}
        post.return_value = response

        call_command("setup_max_webhook")

        post.assert_called_once_with(
            "https://platform-api2.max.ru/subscriptions",
            headers={
                "Authorization": "test-token",
                "Content-Type": "application/json",
            },
            json={
                "url": "https://events.example.com/webhooks/max/",
                "update_types": ["bot_started"],
                "secret": "webhook_secret_123",
            },
            timeout=15,
        )
        response.raise_for_status.assert_called_once_with()

    @override_settings(
        MAX_DEMO_MODE=False,
        MAX_BOT_TOKEN="test-token",
        MAX_WEBHOOK_URL="http://events.example.com/webhooks/max/",
        MAX_WEBHOOK_SECRET="webhook_secret_123",
    )
    def test_webhook_setup_rejects_non_https_url(self):
        with self.assertRaises(CommandError):
            call_command("setup_max_webhook")
