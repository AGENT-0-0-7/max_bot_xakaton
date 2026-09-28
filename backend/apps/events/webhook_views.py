import logging

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.bot_service import send_max_bot_message

logger = logging.getLogger(__name__)


class MaxWebhookView(APIView):
    """
    Receives MAX bot updates after the production webhook is registered.

    It handles onboarding; event confirmations are sent by the event API, so a
    temporary delivery failure never rolls back a confirmed reservation.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        expected_secret = settings.MAX_WEBHOOK_SECRET
        supplied_secret = request.headers.get("X-Max-Webhook-Secret")
        if expected_secret and supplied_secret != expected_secret:
            return Response(
                {"detail": "Invalid webhook secret"},
                status=status.HTTP_403_FORBIDDEN,
            )

        update_type = request.data.get("update_type")
        user = request.data.get("user") or {}
        user_id = user.get("user_id")
        if update_type == "bot_started" and user_id:
            send_max_bot_message(
                user_id,
                "Откройте мини-приложение «Рядом» и найдите событие поблизости.",
            )
        else:
            logger.info("MAX update accepted: %s", update_type)
        return Response({"ok": True}, status=status.HTTP_200_OK)
