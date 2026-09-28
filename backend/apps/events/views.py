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

        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)

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
            return Response(
                {"detail": "Invalid radius"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not 0.1 <= radius_km <= 100:
            return Response(
                {"detail": "Radius must be between 0.1 and 100 km"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if bool(lat) != bool(lon):
            return Response(
                {"detail": "Both latitude and longitude are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)
            except ValueError:
                return Response(
                    {"detail": "Invalid coordinates"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                return Response(
                    {"detail": "Coordinates are outside valid ranges"},
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
        may_view_unpublished = (
            request.user
            and not request.user.is_anonymous
            and (
                request.user.is_staff
                or event.organizer_id == request.user.id
            )
        )
        if event.status != EventStatus.APPROVED and not may_view_unpublished:
            return Response(
                {"detail": "Event is not available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = EventDetailSerializer(event, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        event = get_object_or_404(Event, pk=pk)
        with transaction.atomic():
            event_locked = Event.objects.select_for_update().get(pk=event.pk)
            if event_locked.status != EventStatus.APPROVED:
                return Response(
                    {"detail": "Event is not open for registration"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if event_locked.start_time <= timezone.now():
                return Response(
                    {"detail": "Event has already started"},
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
                        "registration_id": registration.id,
                    },
                    status=status.HTTP_200_OK,
                )

            registrations_count = Registration.objects.filter(
                event=event_locked
            ).count()
            if registrations_count > event_locked.max_participants:
                registration.delete()
                return Response(
                    {"status": "error", "message": "No available seats"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        notification_sent = send_max_bot_message(
            request.user.max_id,
            'Вы записаны на «{}».\nАдрес: {}\nНачало: {}'.format(
                event.title,
                event.address,
                event.start_time.strftime("%d.%m.%Y %H:%M"),
            ),
        )
        return Response(
            {
                "status": "success",
                "message": (
                    "Registration confirmed"
                    if notification_sent
                    else "Registration confirmed; MAX notification is unavailable"
                ),
                "registration_id": registration.id,
                "notification_sent": notification_sent,
            },
            status=status.HTTP_200_OK,
        )


class EventRegistrationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, *args, **kwargs):
        event = get_object_or_404(Event, pk=pk)
        if event.start_time <= timezone.now():
            return Response(
                {"detail": "Registration can no longer be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        registration = Registration.objects.filter(
            user=request.user, event=event
        ).first()
        if not registration:
            return Response(
                {"detail": "Registration not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        registration.delete()
        return Response(
            {"status": "success", "message": "Registration cancelled"},
            status=status.HTTP_200_OK,
        )


class OrganizerEventsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        events = Event.objects.filter(organizer=request.user).order_by(
            "-created_at"
        )
        serializer = EventListSerializer(
            events, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        event = get_object_or_404(Event, pk=pk)
        if event.organizer_id != request.user.id and not request.user.is_staff:
            return Response(
                {"detail": "Only the organizer can cancel the event"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if event.start_time <= timezone.now():
            return Response(
                {"detail": "Started events cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event.status = EventStatus.CANCELLED
        event.save(update_fields=["status"])
        return Response(
            {"status": "success", "message": "Event cancelled"},
            status=status.HTTP_200_OK,
        )
