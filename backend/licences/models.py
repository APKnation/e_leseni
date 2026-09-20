import secrets
from datetime import date

from django.conf import settings
from django.db import models
from django.utils import timezone


class Licence(models.Model):
    """An issued business licence with a QR-verifiable token."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        EXPIRED = 'EXPIRED', 'Expired'
        RENEWAL_PENDING = 'RENEWAL_PENDING', 'Renewal pending'
        REVOKED = 'REVOKED', 'Revoked'

    application = models.OneToOneField(
        'applications.Application', on_delete=models.PROTECT, related_name='licence'
    )
    licence_number = models.CharField(max_length=60, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    business_name = models.CharField(max_length=200)
    holder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='licences'
    )
    licence_type = models.ForeignKey('lga.LicenceType', on_delete=models.PROTECT, related_name='licences')
    lga = models.ForeignKey('lga.LGA', on_delete=models.PROTECT, related_name='licences')
    issued_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateField(default=date.today)
    valid_until = models.DateField()
    qr_token = models.CharField(max_length=64, unique=True, blank=True)
    revoked_reason = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f'{self.licence_number or "(pending)"} - {self.business_name} ({self.status})'

    def save(self, *args, **kwargs):
        if not self.licence_number:
            self.licence_number = self._generate_licence_number()
        if not self.qr_token:
            self.qr_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def _generate_licence_number(self):
        year = timezone.now().year
        prefix = f'LIC-{self.licence_type.code}-{year}-'
        last = (
            Licence.objects.filter(licence_number__startswith=prefix)
            .order_by('licence_number')
            .values_list('licence_number', flat=True)
            .last()
        )
        seq = int(last.rsplit('-', 1)[-1]) + 1 if last else 1
        return f'{prefix}{seq:05d}'

    @property
    def is_expired(self):
        return self.valid_until < date.today()

    @property
    def days_until_expiry(self):
        return (self.valid_until - date.today()).days


class Renewal(models.Model):
    """A renewal request for an issued licence."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending review'
        APPROVED = 'APPROVED', 'Approved (payment pending)'
        PAID = 'PAID', 'Paid'
        ISSUED = 'ISSUED', 'Renewed licence issued'
        REJECTED = 'REJECTED', 'Rejected'

    licence = models.ForeignKey(Licence, on_delete=models.PROTECT, related_name='renewals')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='licence_renewals'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    fee_paid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    new_valid_until = models.DateField(null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f'Renewal for {self.licence.licence_number} ({self.get_status_display()})'
