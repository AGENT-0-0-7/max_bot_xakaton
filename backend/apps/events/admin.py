from django.contrib import admin

from apps.events.models import Event, Registration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "organizer",
        "status",
        "start_time",
        "max_participants",
    )
    list_filter = ("status", "category")
    search_fields = ("title", "address", "description")
    ordering = ("-start_time",)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "event", "registered_at")
    search_fields = ("user__username", "event__title")
    ordering = ("-registered_at",)
