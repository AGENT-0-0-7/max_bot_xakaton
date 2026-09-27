from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.events.models import Event, EventCategory, EventStatus

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data for the Locator Events app."

    def handle(self, *args, **options):
        admin_user, admin_created = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
                "email": "admin@example.com",
            },
        )
        if admin_created:
            admin_user.set_password("admin_pass")
            admin_user.save()

        organizer, _ = User.objects.get_or_create(
            username="test_organizer",
            defaults={
                "first_name": "Test",
                "last_name": "Organizer",
                "email": "organizer@example.com",
            },
        )
        if not organizer.has_usable_password():
            organizer.set_password("organizer_pass")
            organizer.save()

        sample_events = [
            {
                "title": "IT-Лекторий: Архитектура Microservices",
                "description": "Лекция про микросервисы и production architecture.",
                "category": EventCategory.EDUCATION,
                "address": "ул. Перекопская, 155, Тюмень",
                "latitude": 57.1554,
                "longitude": 65.5241,
                "start_time": timezone.now() + timedelta(days=1, hours=5),
                "end_time": timezone.now() + timedelta(days=1, hours=7),
                "max_participants": 40,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Турнир по настольному теннису",
                "description": "Открытый турнир для студентов и жителей района.",
                "category": EventCategory.SPORT,
                "address": "Спортивный комплекс, Тюмень",
                "latitude": 57.1501,
                "longitude": 65.5482,
                "start_time": timezone.now() + timedelta(days=2, hours=3),
                "end_time": timezone.now() + timedelta(days=2, hours=5),
                "max_participants": 20,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Волонтерский сбор: Уборка парка",
                "description": "Акция по благоустройству общественного пространства.",
                "category": EventCategory.VOLUNTEERING,
                "address": "Затюменский экопарк, Тюмень",
                "latitude": 57.1592,
                "longitude": 65.4711,
                "start_time": timezone.now() + timedelta(days=3, hours=10),
                "end_time": timezone.now() + timedelta(days=3, hours=13),
                "max_participants": 35,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Пикник у набережной",
                "description": "Прогулка, музыка и настольные игры.",
                "category": EventCategory.PARTY,
                "address": "Набережная реки Туры, Тюмень",
                "latitude": 57.1455,
                "longitude": 65.5339,
                "start_time": timezone.now() + timedelta(days=4, hours=18),
                "end_time": timezone.now() + timedelta(days=4, hours=21),
                "max_participants": 30,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Культурный вечер: Indie night",
                "description": "Встреча любителей локальной музыки и искусства.",
                "category": EventCategory.CULTURE,
                "address": "Центральный дворец культуры, Тюмень",
                "latitude": 57.1529,
                "longitude": 65.5352,
                "start_time": timezone.now() + timedelta(days=5, hours=19),
                "end_time": timezone.now() + timedelta(days=5, hours=22),
                "max_participants": 25,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Круглый стол: Город и молодежь",
                "description": "Диалог о развитии городской среды и общественных инициатив.",
                "category": EventCategory.EDUCATION,
                "address": "ТюмГУ, корпус гуманитарных наук",
                "latitude": 57.1531,
                "longitude": 65.5320,
                "start_time": timezone.now() + timedelta(days=6, hours=16),
                "end_time": timezone.now() + timedelta(days=6, hours=18),
                "max_participants": 50,
                "status": EventStatus.PENDING,
            },
            {
                "title": "Пробежка по реке Тура",
                "description": "Утренняя групповая пробежка для всех желающих.",
                "category": EventCategory.SPORT,
                "address": "Пешеходный мост, Набережная, Тюмень",
                "latitude": 57.1482,
                "longitude": 65.5401,
                "start_time": timezone.now() + timedelta(days=1, hours=8),
                "end_time": timezone.now() + timedelta(days=1, hours=10),
                "max_participants": 18,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Рисуем город вместе",
                "description": "Мастер-класс по уличной живописи и граффити.",
                "category": EventCategory.CULTURE,
                "address": "Гилевская роща, Тюмень",
                "latitude": 57.1604,
                "longitude": 65.5078,
                "start_time": timezone.now() + timedelta(days=2, hours=14),
                "end_time": timezone.now() + timedelta(days=2, hours=17),
                "max_participants": 22,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Субботний беговой клуб",
                "description": "Пробежка на небольшие дистанции с разминочной программой.",
                "category": EventCategory.SPORT,
                "address": "Стадион на ул. Мельникайте, Тюмень",
                "latitude": 57.1477,
                "longitude": 65.5614,
                "start_time": timezone.now() + timedelta(days=4, hours=9),
                "end_time": timezone.now() + timedelta(days=4, hours=11),
                "max_participants": 24,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Вечер настолок на ТюмГУ",
                "description": "Раунд игр, чай и новые знакомства.",
                "category": EventCategory.PARTY,
                "address": "Кампус ТюмГУ, основное здание",
                "latitude": 57.1549,
                "longitude": 65.5285,
                "start_time": timezone.now() + timedelta(days=7, hours=18),
                "end_time": timezone.now() + timedelta(days=7, hours=22),
                "max_participants": 28,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Маршрут по экопарку",
                "description": "Гид-тур по зелёным аллеям и местам отдыха.",
                "category": EventCategory.CULTURE,
                "address": "Эко-парк Затюменский, Тюмень",
                "latitude": 57.1611,
                "longitude": 65.4673,
                "start_time": timezone.now() + timedelta(days=5, hours=12),
                "end_time": timezone.now() + timedelta(days=5, hours=15),
                "max_participants": 15,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Практикум по Python для начинающих",
                "description": "Мини-курс по азам программирования и первым проектам.",
                "category": EventCategory.EDUCATION,
                "address": "Ул. Ленина, 88, Тюмень",
                "latitude": 57.1526,
                "longitude": 65.5355,
                "start_time": timezone.now() + timedelta(days=8, hours=17),
                "end_time": timezone.now() + timedelta(days=8, hours=20),
                "max_participants": 30,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Волонтерский субботник",
                "description": "Сбор участников для уборки и озеленения района.",
                "category": EventCategory.VOLUNTEERING,
                "address": "Сквер им. Ленина, Тюмень",
                "latitude": 57.1513,
                "longitude": 65.5312,
                "start_time": timezone.now() + timedelta(days=3, hours=11),
                "end_time": timezone.now() + timedelta(days=3, hours=14),
                "max_participants": 40,
                "status": EventStatus.APPROVED,
            },
            {
                "title": "Фестиваль командных игр",
                "description": "Игры и активности для студентов и жителей кампуса.",
                "category": EventCategory.PARTY,
                "address": "ТюмГУ, спортивный двор",
                "latitude": 57.1547,
                "longitude": 65.5273,
                "start_time": timezone.now() + timedelta(days=9, hours=16),
                "end_time": timezone.now() + timedelta(days=9, hours=20),
                "max_participants": 45,
                "status": EventStatus.APPROVED,
            },
        ]

        for payload in sample_events:
            event, created = Event.objects.get_or_create(
                title=payload["title"],
                defaults={
                    "organizer": organizer,
                    "description": payload["description"],
                    "category": payload["category"],
                    "address": payload["address"],
                    "latitude": payload["latitude"],
                    "longitude": payload["longitude"],
                    "start_time": payload["start_time"],
                    "end_time": payload["end_time"],
                    "max_participants": payload["max_participants"],
                    "status": payload["status"],
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created event: {event.title}")
                )

        self.stdout.write(self.style.SUCCESS("Seed data loaded successfully."))
