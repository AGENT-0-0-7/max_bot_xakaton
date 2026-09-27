from django.db.models.signals import pre_save
from django.dispatch import receiver
from apps.events.models import Event, EventStatus
from apps.events.bot_service import send_max_bot_message

@receiver(pre_save, sender=Event)
def notify_organizer_on_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # New event creation handled separately if needed

    try:
        old_instance = Event.objects.get(pk=instance.pk)
    except Event.DoesNotExist:
        return

    if old_instance.status != instance.status:
        organizer = instance.organizer
        if organizer and organizer.max_id:
            if instance.status == EventStatus.APPROVED:
                msg = (
                    f"🎉 <b>Событие одобрено!</b>\n\n"
                    f"Ваше событие <b>«{instance.title}»</b> прошло модерацию и теперь отображается на карте Локатора Событий!"
                )
                send_max_bot_message(organizer.max_id, msg)
            elif instance.status == EventStatus.REJECTED:
                msg = (
                    f"❌ <b>Событие не прошло модерацию</b>\n\n"
                    f"К сожалению, событие <b>«{instance.title}»</b> было отклонено модератором."
                )
                send_max_bot_message(organizer.max_id, msg)
