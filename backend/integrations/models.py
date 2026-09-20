from django.db import models


class IntegrationLog(models.Model):
    """Audit log of every call made to/from external systems (BRELA, TRA, GePG)."""

    class System(models.TextChoices):
        BRELA = 'BRELA', 'BRELA'
        TRA = 'TRA', 'TRA'
        GEPG = 'GePG', 'Government Electronic Payment Gateway'
        USSD = 'USSD', 'USSD Gateway'

    class Direction(models.TextChoices):
        OUTBOUND = 'OUTBOUND', 'Outbound request'
        INBOUND = 'INBOUND', 'Inbound (mock response)'

    system = models.CharField(max_length=10, choices=System.choices)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    endpoint = models.CharField(max_length=255)
    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    is_success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.system} {self.direction} {self.endpoint} ({"OK" if self.is_success else "FAIL"})'
