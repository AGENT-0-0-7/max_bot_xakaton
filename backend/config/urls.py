from django.contrib import admin
from django.urls import include, path

from apps.events.webhook_views import MaxWebhookView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.events.urls")),
    path("webhooks/max/", MaxWebhookView.as_view(), name="max-webhook"),
]
