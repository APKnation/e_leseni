from django.contrib import admin

from .models import IntegrationLog


@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = ('system', 'direction', 'endpoint', 'is_success', 'status_code', 'created_at')
    list_filter = ('system', 'direction', 'is_success')
    search_fields = ('endpoint', 'error_message')
    readonly_fields = (
        'system', 'direction', 'endpoint', 'request_payload',
        'response_payload', 'status_code', 'is_success', 'error_message', 'created_at',
    )

    def has_add_permission(self, request):
        return False
