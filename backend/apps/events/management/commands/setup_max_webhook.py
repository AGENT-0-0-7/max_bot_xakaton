import re
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Register the MAX bot webhook for bot_started updates."

    def handle(self, *args, **options):
        if settings.MAX_DEMO_MODE:
            raise CommandError(
                "Disable MAX_DEMO_MODE before registering a real webhook."
            )
        if not settings.MAX_BOT_TOKEN:
            raise CommandError("MAX_BOT_TOKEN is required.")
        if not settings.MAX_WEBHOOK_URL:
            raise CommandError(
                "Set MAX_WEBHOOK_URL to the public HTTPS webhook URL."
            )
        if not settings.MAX_WEBHOOK_SECRET:
            raise CommandError("MAX_WEBHOOK_SECRET is required.")
        if not re.fullmatch(
            r"[A-Za-z0-9_-]{5,256}", settings.MAX_WEBHOOK_SECRET
        ):
            raise CommandError(
                "MAX_WEBHOOK_SECRET must be 5-256 letters, digits, _ or -."
            )

        parsed_url = urlparse(settings.MAX_WEBHOOK_URL)
        if (
            parsed_url.scheme != "https"
            or not parsed_url.hostname
            or parsed_url.port not in (None, 443)
        ):
            raise CommandError(
                "MAX_WEBHOOK_URL must use HTTPS on the default port 443."
            )

        try:
            response = requests.post(
                "{}/subscriptions".format(settings.MAX_BOT_API_URL),
                headers={
                    "Authorization": settings.MAX_BOT_TOKEN,
                    "Content-Type": "application/json",
                },
                json={
                    "url": settings.MAX_WEBHOOK_URL,
                    "update_types": ["bot_started"],
                    "secret": settings.MAX_WEBHOOK_SECRET,
                },
                timeout=15,
            )
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as error:
            raise CommandError(
                "MAX webhook registration request failed: {}".format(error)
            ) from error
        except ValueError as error:
            raise CommandError(
                "MAX returned a response that is not JSON."
            ) from error

        if not result.get("success"):
            raise CommandError(
                "MAX rejected webhook registration: {}".format(
                    result.get("message", "unknown error")
                )
            )
        self.stdout.write(
            self.style.SUCCESS(
                "MAX webhook registered at {}".format(settings.MAX_WEBHOOK_URL)
            )
        )
