from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.bot_service import send_max_bot_message
from apps.events.models import Event, EventStatus, Registration
from apps.events.serializers import (
    EventCreateSerializer,
    EventDetailSerializer,
    EventListSerializer,
)


class EventListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        qs = Event.objects.filter(
            status=EventStatus.APPROVED, start_time__gte=timezone.now()
        ).order_by("start_time")

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        radius_km = (
            request.query_params.get("radius_km")
            or request.query_params.get("radius")
            or "25"
        )

        try:
            radius_km = float(radius_km)
        except ValueError:
            radius_km = 25.0

        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)
            except ValueError:
                return Response(
                    {"detail": "Invalid coordinates"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            event_rows = []
            for event in qs:
                distance_km = event.calculate_distance_km(lat, lon)
                if distance_km <= radius_km:
                    event_rows.append((event, distance_km))
            event_rows.sort(key=lambda item: item[1])
            events = [event for event, _ in event_rows]
        else:
            events = list(qs)

        serializer = EventListSerializer(
            events, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if not request.user or request.user.is_anonymous:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = EventCreateSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        event = serializer.save()
        return Response(
            {
                "id": event.id,
                "status": event.status,
                "message": "Event submitted for moderation",
            },
            status=status.HTTP_201_CREATED,
        )


class EventDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk, *args, **kwargs):
        event = get_object_or_404(Event, pk=pk)
        serializer = EventDetailSerializer(event, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        event = get_object_or_404(Event, pk=pk)

        if event.status != EventStatus.APPROVED:
            return Response(
                {"detail": "Event is not open for registration"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if event.start_time <= timezone.now():
            return Response(
                {"detail": "Event has already started"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            event_locked = Event.objects.select_for_update().get(pk=event.pk)
            registrations_count = Registration.objects.filter(
                event=event_locked
            ).count()

            if registrations_count >= event_locked.max_participants:
                return Response(
                    {"status": "error", "message": "No available seats"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            registration, created = Registration.objects.get_or_create(
                user=request.user, event=event_locked
            )
            if not created:
                return Response(
                    {
                        "status": "success",
                        "message": "You are already registered",
                    },
                    status=status.HTTP_200_OK,
                )

        send_max_bot_message(
            request.user.max_id,
            f'🎟️ Вы успешно записались на событие "{event.title}". \nАдрес: {event.address}\nВремя: {event.start_time.strftime("%d.%m.%Y %H:%M")}',
        )

        return Response(
            {
                "status": "success",
                "message": "You have successfully registered",
            },
            status=status.HTTP_200_OK,
        )


class UserRegistrationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        registrations = (
            Registration.objects.filter(user=request.user)
            .select_related("event")
            .order_by("-registered_at")
        )
        data = []
        for registration in registrations:
            data.append(
                {
                    "id": registration.id,
                    "event_id": registration.event.id,
                    "title": registration.event.title,
                    "status": registration.event.status,
                    "address": registration.event.address,
                    "start_time": registration.event.start_time,
                    "registered_at": registration.registered_at,
                }
            )
        return Response(data, status=status.HTTP_200_OK)
