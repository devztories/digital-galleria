from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'name', 'email', 'phone', 'gender', 'theme', 'is_staff', 'created_at')
    list_filter = ('gender', 'theme', 'is_staff', 'is_active')
    search_fields = ('username', 'name', 'email', 'phone')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Digital Galleria Profile', {'fields': ('name', 'phone', 'gender', 'theme', 'profile_image')}),
    )
