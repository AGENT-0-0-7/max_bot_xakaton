from functools import partial

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.events.bot_service import send_max_bot_message
from apps.events.models import Event, EventStatus


@receiver(pre_save, sender=Event)
def remember_event_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return

    instance._previous_status = (
        Event.objects.filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
    )


@receiver(post_save, sender=Event)
def notify_organizer_on_status_change(sender, instance, created, **kwargs):
    previous_status = getattr(instance, "_previous_status", None)
    if created or previous_status == instance.status or not instance.organizer_id:
        return

    organizer = instance.organizer
    if not organizer.max_id:
        return

    if instance.status == EventStatus.APPROVED:
        message = (
            f"Событие «{instance.title}» одобрено и появилось "
            "в ленте «Рядом»."
        )
    elif instance.status == EventStatus.REJECTED:
        message = f"Событие «{instance.title}» отклонено модератором."
    else:
        return

    transaction.on_commit(
        partial(send_max_bot_message, organizer.max_id, message)
    )
