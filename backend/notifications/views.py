from rest_framework import permissions, viewsets

from .models import SMSLog
from .serializers import SMSLogSerializer


class SMSLogViewSet(viewsets.ReadOnlyModelViewSet):
    """SMS log; staff only (applicant phone numbers are sensitive)."""

    queryset = SMSLog.objects.select_related('user', 'application').all()
    serializer_class = SMSLogSerializer
    filterset_fields = ['status', 'purpose', 'user', 'application']
    search_fields = ['recipient', 'body', 'provider_message_id']
    permission_classes = [permissions.IsAdminUser]
