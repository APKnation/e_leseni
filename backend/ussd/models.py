from django.conf import settings
from django.db import models


class USSDSession(models.Model):
    """One USSD dialogue: identified by session_id from the gateway.

    Stores the current menu state and any in-progress input (e.g. the
    licence type the user is applying for) so each gateway request can be
    handled statelessly.
    """

    class State(models.TextChoices):
        START = 'START', 'Main menu'
        APPLY_LGA = 'APPLY_LGA', 'Apply: pick council'
        APPLY_LICENCE = 'APPLY_LICENCE', 'Apply: pick licence'
        APPLY_BUSINESS = 'APPLY_BUSINESS', 'Apply: pick business'
        APPLY_PURPOSE = 'APPLY_PURPOSE', 'Apply: purpose / confirm'
        STATUS_SELECT = 'STATUS_SELECT', 'Status: pick application'
        PAY_SELECT_INVOICE = 'PAY_SELECT_INVOICE', 'Pay: pick invoice'
        PAY_AMOUNT = 'PAY_AMOUNT', 'Pay: amount'
        PAY_PHONE = 'PAY_PHONE', 'Pay: phone'
        EXITED = 'EXITED', 'Ended'

    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    phone_number = models.CharField(max_length=15, db_index=True)
    state = models.CharField(max_length=30, choices=State.choices, default=State.START)
    context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.phone_number} ({self.state})'
