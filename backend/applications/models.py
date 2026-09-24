import django.dispatch
from django.conf import settings
from django.db import models
from django.utils import timezone

from core_docs.validation import validate_pdf_document

# Sent by Application.transition_to() after every successful status change.
# receivers should mutate other apps (invoices, licences, SMS) — never the app itself.
application_status_changed = django.dispatch.Signal()  # provides: application, old_status, new_status, changed_by


class Application(models.Model):
    """A licence application moving through the e-Leseni status flow.

    Main line:
        DRAFT -> SUBMITTED -> UNDER_REVIEW -> INSPECTION_SCHEDULED -> INSPECTED
              -> APPROVED -> PAYMENT_PENDING -> PAID -> ISSUED

    Side branches:
        SUBMITTED/UNDER_REVIEW/INSPECTED -> RETURNED_FOR_CORRECTION -> DRAFT
        UNDER_REVIEW/INSPECTED -> REJECTED
    """

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under review'
        INSPECTION_SCHEDULED = 'INSPECTION_SCHEDULED', 'Inspection scheduled'
        INSPECTED = 'INSPECTED', 'Inspected'
        APPROVED = 'APPROVED', 'Approved'
        PAYMENT_PENDING = 'PAYMENT_PENDING', 'Payment pending'
        PAID = 'PAID', 'Paid'
        ISSUED = 'ISSUED', 'Issued'
        RETURNED_FOR_CORRECTION = 'RETURNED_FOR_CORRECTION', 'Returned for correction'
        REJECTED = 'REJECTED', 'Rejected'

    TRANSITIONS = {
        Status.DRAFT: {Status.SUBMITTED},
        Status.SUBMITTED: {Status.UNDER_REVIEW, Status.RETURNED_FOR_CORRECTION},
        Status.UNDER_REVIEW: {
            Status.INSPECTION_SCHEDULED,
            Status.RETURNED_FOR_CORRECTION,
            Status.REJECTED,
        },
        Status.INSPECTION_SCHEDULED: {Status.INSPECTED},
        Status.INSPECTED: {Status.APPROVED, Status.REJECTED, Status.RETURNED_FOR_CORRECTION},
        Status.APPROVED: {Status.PAYMENT_PENDING},
        Status.PAYMENT_PENDING: {Status.PAID},
        Status.PAID: {Status.ISSUED},
        Status.ISSUED: set(),
        Status.RETURNED_FOR_CORRECTION: {Status.DRAFT},
        Status.REJECTED: set(),
    }

    class Priority(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        URGENT = 'URGENT', 'Urgent'

    reference_number = models.CharField(max_length=60, unique=True, blank=True)
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='applications'
    )
    business = models.ForeignKey('businesses.Business', on_delete=models.PROTECT, related_name='applications')
    licence_type = models.ForeignKey('lga.LicenceType', on_delete=models.PROTECT, related_name='applications')
    location = models.ForeignKey(
        'businesses.BusinessLocation', on_delete=models.PROTECT, related_name='applications'
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT, db_index=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    purpose_statement = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_applications',
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('review_application', 'Can review applications'),
            ('inspect_application', 'Can conduct inspections'),
            ('approve_application', 'Can approve applications'),
        ]

    def __str__(self):
        return f'{self.reference_number or "DRAFT"} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self._generate_reference_number()
        super().save(*args, **kwargs)

    def _generate_reference_number(self):
        year = timezone.now().year
        prefix = f'EL-{self.licence_type.code}-{year}-'
        last = (
            Application.objects.filter(reference_number__startswith=prefix)
            .order_by('reference_number')
            .values_list('reference_number', flat=True)
            .last()
        )
        seq = int(last.rsplit('-', 1)[-1]) + 1 if last else 1
        return f'{prefix}{seq:05d}'

    # -- status flow -------------------------------------------------------

    @property
    def allowed_next_statuses(self):
        return self.TRANSITIONS[self.Status(self.status)]

    def transition_to(self, new_status, *, by=None, note=''):
        """Move the application to a new status if the transition is valid.

        Creates a StatusHistory entry and stamps the relevant timestamps.
        """
        new_status = self.Status(new_status)
        if new_status not in self.allowed_next_statuses:
            raise ValueError(
                f'Invalid transition {self.status} -> {new_status}. '
                f'Allowed: {sorted(s.value for s in self.allowed_next_statuses)}'
            )

        old_status = self.status
        self.status = new_status
        if new_status == self.Status.SUBMITTED:
            self.submitted_at = timezone.now()
        elif new_status in (self.Status.APPROVED, self.Status.REJECTED):
            self.decided_at = timezone.now()
        if note:
            self.rejection_reason = note if new_status == self.Status.REJECTED else self.rejection_reason
        self.save(update_fields=['status', 'submitted_at', 'decided_at', 'rejection_reason', 'updated_at'])

        StatusHistory.objects.create(
            application=self, from_status=old_status, to_status=new_status, changed_by=by, note=note
        )
        application_status_changed.send(
            sender=self.__class__, application=self, old_status=old_status, new_status=new_status, changed_by=by
        )
        return self

    def can_transition_to(self, new_status):
        return self.Status(new_status) in self.allowed_next_statuses


class ApplicationDocument(models.Model):
    """Documents attached to an application, mapped to licence-type requirements."""

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    requirement = models.ForeignKey(
        'lga.Requirement', null=True, blank=True, on_delete=models.SET_NULL, related_name='application_documents'
    )
    file = models.FileField(
        upload_to='application_documents/%Y/%m/', validators=[validate_pdf_document]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        req = self.requirement.name if self.requirement else 'Other'
        return f'{self.application.reference_number}: {req}'


class StatusHistory(models.Model):
    """Audit trail of every status change on an application."""

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='history')
    from_status = models.CharField(max_length=30, choices=Application.Status.choices)
    to_status = models.CharField(max_length=30, choices=Application.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='status_changes'
    )
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['changed_at']
        verbose_name_plural = 'status histories'

    def __str__(self):
        return f'{self.application.reference_number}: {self.from_status} -> {self.to_status}'


class Inspection(models.Model):
    """A field inspection scheduled for an application."""

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='inspections')
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='inspections'
    )
    scheduled_for = models.DateTimeField()
    conducted_at = models.DateTimeField(null=True, blank=True)
    findings = models.TextField(blank=True)
    passed = models.BooleanField(null=True, blank=True, help_text='Null until the inspection is conducted.')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_accuracy = models.FloatField(null=True, blank=True, help_text='Accuracy in meters')
    inspector_signature_hash = models.CharField(max_length=64, blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-scheduled_for']

    def __str__(self):
        return f'Inspection for {self.application.reference_number} on {self.scheduled_for:%Y-%m-%d}'


class InspectionPhoto(models.Model):
    """Time-stamped and geotagged photo evidence from an inspection."""

    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='photos')
    checklist_item = models.ForeignKey(
        'lga.InspectionChecklistItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='photos'
    )
    photo = models.FileField(upload_to='inspection_photos/%Y/%m/')
    client_capture_time = models.DateTimeField()
    server_receipt_time = models.DateTimeField(auto_now_add=True)
    sha256_hash = models.CharField(max_length=64)
    exif_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['server_receipt_time']

    def __str__(self):
        return f'Photo for {self.inspection} ({self.sha256_hash[:8]})'
