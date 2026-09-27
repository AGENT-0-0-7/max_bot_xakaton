from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.models import Registration
from apps.users.auth_utils import generate_jwt_for_user, validate_max_init_data
from apps.users.serializers import InitDataAuthSerializer, UserSerializer

User = get_user_model()


class MaxAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = InitDataAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        init_data_raw = serializer.validated_data["init_data"]
        user_data = validate_max_init_data(init_data_raw)

        if not user_data:
            return Response(
                {"error": "Invalid initData signature or format"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        max_id = user_data.get("id")
        if not max_id:
            return Response(
                {"error": "Missing user id in initData"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        first_name = user_data.get("first_name", "MAX User")
        last_name = user_data.get("last_name", "")
        username = user_data.get("username") or f"max_user_{max_id}"

        user, created = User.objects.get_or_create(
            max_id=max_id,
            defaults={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        if not created:
            user.first_name = first_name
            user.last_name = last_name
            user.save()

        jwt_token = generate_jwt_for_user(user)

        return Response(
            {"access_token": jwt_token, "user": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRegistrationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        registrations = (
            Registration.objects.filter(user=request.user)
            .select_related("event")
            .order_by("-registered_at")
        )
        payload = []
        for item in registrations:
            payload.append(
                {
                    "id": item.id,
                    "event_id": item.event.id,
                    "title": item.event.title,
                    "status": item.event.status,
                    "address": item.event.address,
                    "start_time": item.event.start_time,
                    "registered_at": item.registered_at,
                }
            )
        return Response(payload, status=status.HTTP_200_OK)
