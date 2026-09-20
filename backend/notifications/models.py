from django.conf import settings
from django.db import models


class SMSLog(models.Model):
    """Every SMS the system attempts to send, for auditing and the SMS log UI."""

    class Purpose(models.TextChoices):
        SUBMISSION = 'SUBMISSION', 'Application submitted'
        CORRECTION = 'CORRECTION', 'Returned for correction'
        APPROVAL = 'APPROVAL', 'Application approved'
        CONTROL_NUMBER = 'CONTROL_NUMBER', 'Control number issued'
        PAYMENT_CONFIRMED = 'PAYMENT_CONFIRMED', 'Payment confirmed'
        ISSUANCE = 'ISSUANCE', 'Licence issued'
        REJECTION = 'REJECTION', 'Application rejected'
        RENEWAL = 'RENEWAL', 'Renewal update'
        GENERAL = 'GENERAL', 'General'

    class Status(models.TextChoices):
        QUEUED = 'QUEUED', 'Queued'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    recipient = models.CharField(max_length=15)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='sms_logs'
    )
    application = models.ForeignKey(
        'applications.Application', null=True, blank=True, on_delete=models.SET_NULL, related_name='sms_logs'
    )
    purpose = models.CharField(max_length=20, choices=Purpose.choices, default=Purpose.GENERAL)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED, db_index=True)
    backend = models.CharField(max_length=100, blank=True, help_text='SMS backend used to send.')
    provider_message_id = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'SMS log entry'
        verbose_name_plural = 'SMS log entries'

    def __str__(self):
        return f'{self.recipient} ({self.purpose}, {self.status})'
