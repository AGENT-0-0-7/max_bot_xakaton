from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users.models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'max_id', 'username', 'first_name', 'last_name', 'is_staff', 'created_at')
    search_fields = ('max_id', 'username', 'first_name', 'last_name')
    ordering = ('-id',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('MAX Info', {'fields': ('max_id',)}),
    )
