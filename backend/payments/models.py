from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Invoice(models.Model):
    """A bill for a licence application, settled through GePG.

    Lifecycle: PENDING -> control number requested -> WAITING_PAYMENT
    -> paid (reconciled) -> PAID. Cancelled invoices are terminal.
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending (control number not yet requested)'
        WAITING_PAYMENT = 'WAITING_PAYMENT', 'Waiting for payment'
        PAID = 'PAID', 'Paid'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired (control number no longer valid)'

    application = models.OneToOneField(
        'applications.Application', on_delete=models.PROTECT, related_name='invoice'
    )
    control_number = models.CharField(max_length=20, unique=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='TZS')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    gepg_bill_id = models.CharField(max_length=50, blank=True)
    gepg_approval = models.CharField(max_length=100, blank=True, help_text='GePG payment reference / receipt number.')
    issued_at = models.DateTimeField(auto_now_add=True)
    control_number_expires_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f'Invoice {self.control_number or "(pending)"} - {self.application.reference_number} - {self.amount} {self.currency}'

    @property
    def amount_paid(self):
        return self.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

    @property
    def is_fully_paid(self):
        return self.amount_paid >= self.amount

    @property
    def is_settled(self):
        return self.status == self.Status.PAID


class Payment(models.Model):
    """A payment record against an invoice (GePG-style receipt)."""

    class Method(models.TextChoices):
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile money'
        BANK = 'BANK', 'Bank'
        AGENT = 'AGENT', 'Agent'
        CASH = 'CASH', 'Cash (government office)'

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    receipt_number = models.CharField(
        max_length=30, unique=True, blank=True,
        help_text='GePG receipt; empty until reconciliation succeeds.',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.MOBILE_MONEY)
    payer_name = models.CharField(max_length=150, blank=True)
    payer_phone = models.CharField(max_length=15, blank=True)
    reference = models.CharField(max_length=100, blank=True, help_text='External transaction reference (e.g. M-Pesa code).')
    paid_at = models.DateTimeField(default=timezone.now)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.receipt_number or "(unnumbered)"} - {self.amount} {self.invoice.currency}'
