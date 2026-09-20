from rest_framework import serializers

from .models import SMSLog


class SMSLogSerializer(serializers.ModelSerializer):
    recipient_user = serializers.CharField(source='user.username', read_only=True, default=None)
    application_reference = serializers.CharField(
        source='application.reference_number', read_only=True, default=None
    )
    purpose_display = serializers.CharField(source='get_purpose_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SMSLog
        fields = [
            'id', 'recipient', 'recipient_user', 'application', 'application_reference',
            'purpose', 'purpose_display', 'body', 'status', 'status_display', 'backend',
            'provider_message_id', 'error_message', 'created_at', 'sent_at',
        ]
        read_only_fields = fields
