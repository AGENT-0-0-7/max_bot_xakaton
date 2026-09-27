from django.urls import path

from apps.users.views import (
    CurrentUserView,
    MaxAuthView,
    UserRegistrationsView,
)

urlpatterns = [
    path("auth/max/", MaxAuthView.as_view(), name="max-auth"),
    path("users/me/", CurrentUserView.as_view(), name="current-user"),
    path(
        "users/me/registrations/",
        UserRegistrationsView.as_view(),
        name="user-registrations",
    ),
]
