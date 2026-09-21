from django.contrib import admin

from .models import USSDSession


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'state', 'session_id', 'created_at', 'updated_at')
    list_filter = ('state',)
    search_fields = ('phone_number', 'session_id')
    readonly_fields = ('session_id', 'phone_number', 'state', 'context', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False
