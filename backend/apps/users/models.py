from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    max_id = models.BigIntegerField(unique=True, db_index=True, null=True, blank=True, verbose_name="MAX User ID")
    first_name = models.CharField(max_length=150, verbose_name="First Name")
    last_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="Last Name")
    username = models.CharField(max_length=150, null=True, blank=True, unique=True, verbose_name="Username")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        name = f"{self.first_name} {self.last_name or ''}".strip()
        if not name:
            name = self.username or f"User #{self.id}"
        return f"{name} (max_id: {self.max_id})"
