from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone_number', 'lga', 'is_active')
    list_filter = ('role', 'is_active', 'lga')
    search_fields = ('username', 'email', 'phone_number')
    fieldsets = UserAdmin.fieldsets + (
        ('e-Leseni', {'fields': ('role', 'phone_number', 'lga')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('e-Leseni', {'fields': ('role', 'phone_number', 'lga')}),
    )
