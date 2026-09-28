from django.urls import path

from apps.events.views import (
    EventCancelView,
    EventDetailView,
    EventListCreateView,
    EventRegistrationView,
    EventRegisterView,
    OrganizerEventsView,
)

urlpatterns = [
    path("events/", EventListCreateView.as_view(), name="event-list-create"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="event-detail"),
    path(
        "events/<int:pk>/register/",
        EventRegisterView.as_view(),
        name="event-register",
    ),
    path(
        "events/<int:pk>/registration/",
        EventRegistrationView.as_view(),
        name="event-registration",
    ),
    path(
        "events/<int:pk>/cancel/",
        EventCancelView.as_view(),
        name="event-cancel",
    ),
    path(
        "users/me/events/",
        OrganizerEventsView.as_view(),
        name="organizer-events",
    ),
]
