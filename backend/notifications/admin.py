from django.contrib import admin

from .models import SMSLog


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'purpose', 'status', 'application', 'created_at', 'sent_at')
    list_filter = ('purpose', 'status', 'backend')
    search_fields = ('recipient', 'body', 'provider_message_id')
    readonly_fields = (
        'recipient', 'user', 'application', 'purpose', 'body', 'status',
        'backend', 'provider_message_id', 'error_message', 'created_at', 'sent_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
