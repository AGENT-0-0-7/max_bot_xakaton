from django.urls import path

from apps.events.views import (
    EventDetailView,
    EventListCreateView,
    EventRegisterView,
)

urlpatterns = [
    path("events/", EventListCreateView.as_view(), name="event-list-create"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="event-detail"),
    path(
        "events/<int:pk>/register/",
        EventRegisterView.as_view(),
        name="event-register",
    ),
]
