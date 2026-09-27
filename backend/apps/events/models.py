from django.db import models
from django.contrib.auth import get_user_model
import math

User = get_user_model()

class EventCategory(models.TextChoices):
    SPORT = 'sport', 'Спорт'
    CULTURE = 'culture', 'Культура'
    EDUCATION = 'education', 'Обучение'
    PARTY = 'party', 'Развлечения / Квартирники'
    VOLUNTEERING = 'volunteering', 'Волонтерство'

class EventStatus(models.TextChoices):
    PENDING = 'pending', 'На модерации'
    APPROVED = 'approved', 'Одобрено'
    REJECTED = 'rejected', 'Отклонено'
    CANCELLED = 'cancelled', 'Отменено'

class Event(models.Model):
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events', verbose_name='Организатор')
    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    category = models.CharField(max_length=50, choices=EventCategory.choices, verbose_name='Категория')
    address = models.CharField(max_length=255, verbose_name='Адрес')
    latitude = models.FloatField(verbose_name='Широта')
    longitude = models.FloatField(verbose_name='Долгота')
    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    max_participants = models.PositiveIntegerField(verbose_name='Лимит мест')
    status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.PENDING, verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        db_table = 'events'
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['start_time']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def registered_count(self):
        return self.registrations.count()

    @property
    def available_seats(self):
        seats = self.max_participants - self.registered_count
        return max(0, seats)

    def calculate_distance_km(self, lat: float, lon: float) -> float:
        """Haversine formula for distance calculation in kilometers."""
        R = 6371.0  # Earth radius in km
        dlat = math.radians(lat - self.latitude)
        dlon = math.radians(lon - self.longitude)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(self.latitude)) * math.cos(math.radians(lat)) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c


class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations', verbose_name='Пользователь')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations', verbose_name='Событие')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')

    class Meta:
        db_table = 'registrations'
        verbose_name = 'Запись на событие'
        verbose_name_plural = 'Записи на события'
        constraints = [
            models.UniqueConstraint(fields=['user', 'event'], name='unique_user_event_registration')
        ]

    def __str__(self):
        return f"{self.user} -> {self.event.title}"
