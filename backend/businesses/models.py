from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core_docs.validation import validate_pdf_document


class Business(models.Model):
    """A business registered by an applicant on the platform."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='businesses'
    )
    name = models.CharField(max_length=200)
    tin_number = models.CharField(max_length=20, blank=True, help_text='TRA TIN, verified via integrations app.')
    brela_registration_number = models.CharField(max_length=30, blank=True)
    nida_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Owner NIDA captured with the registration (snapshot of the owner\'s NIDA).',
    )
    sector = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False, help_text='Set once BRELA/TRA verification passes.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['owner', 'name'], name='unique_business_name_per_owner'),
        ]

    def __str__(self):
        return self.name

    def ensure_verified(self):
        """Verify TIN with TRA and registration with BRELA via the adapters.

        Prerequisites (real-council rules): a TRA TIN, a BRELA registration
        number, the owner's NIDA, and the street identification letter on
        file. Marks the business verified only if everything passes; returns
        whether the business ends up verified.
        """
        from integrations.adapters import BRELAdapter, TRAAdapter

        if self.is_verified:
            return True
        if (
            not self.tin_number
            or not self.brela_registration_number
            or not self.owner.nida_number
            or not self.documents.filter(kind=BusinessDocument.Kinds.STREET_ID_LETTER).exists()
        ):
            return False
        tin_result = TRAAdapter().verify_tin(self.tin_number, self.name)
        brela_result = BRELAdapter().verify_registration(
            self.brela_registration_number, self.name
        )
        verified = (
            tin_result.success and tin_result.data.get('valid') is True
            and brela_result.success and brela_result.data.get('registered') is True
        )
        if verified:
            self.is_verified = True
            self.save(update_fields=['is_verified', 'updated_at'])
        return verified


class TINApplication(models.Model):
    """A TIN application submitted to TRA (demo workflow; mirrors TRA ITAX)."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tin_applications'
    )
    business_name = models.CharField(max_length=200)
    taxpayer_name = models.CharField(max_length=200)
    # Real TRA asks for the applicant's TIN-carrying national ID number on the form.
    nida_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='National ID number of the taxpayer, as printed on the NIDA card.',
    )
    tin_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'TIN application for {self.business_name} ({self.status})'


class TINApplicationDocument(models.Model):
    """Supporting documents for a TIN application (NIDA copy, etc.).

    Real TRA requires a copy of the national ID with every TIN application.
    """

    class Kinds(models.TextChoices):
        NIDA_COPY = 'NIDA_COPY', 'Copy of National ID (NIDA)'
        PASSPORT_PHOTO = 'PASSPORT_PHOTO', 'Passport-size photo'
        OTHER = 'OTHER', 'Other'

    tin_application = models.ForeignKey(
        TINApplication, on_delete=models.CASCADE, related_name='documents'
    )
    kind = models.CharField(max_length=30, choices=Kinds.choices, default=Kinds.OTHER)
    file = models.FileField(
        upload_to='tin_applications/%Y/%m/', validators=[validate_pdf_document]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f'{self.get_kind_display()} - TIN app {self.tin_application_id}'


class BusinessLocation(models.Model):
    """Physical location of a business within an LGA."""

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='locations')
    lga = models.ForeignKey('lga.LGA', on_delete=models.PROTECT, related_name='business_locations')
    ward = models.CharField(max_length=100)
    street = models.CharField(max_length=150)
    plot_number = models.CharField(max_length=50, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_primary', 'ward']

    def __str__(self):
        return f'{self.business.name} - {self.ward}, {self.street}'


class BusinessDocument(models.Model):
    """Supporting documents attached to a business (e.g. TIN certificate)."""

    class Kinds(models.TextChoices):
        TIN_CERTIFICATE = 'TIN_CERTIFICATE', 'TIN Certificate'
        BRELA_CERTIFICATE = 'BRELA_CERTIFICATE', 'BRELA Registration Certificate'
        STREET_ID_LETTER = 'STREET_ID_LETTER', 'Street Identification Letter'
        LEASE_AGREEMENT = 'LEASE_AGREEMENT', 'Lease Agreement'
        OTHER = 'OTHER', 'Other'

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='documents')
    kind = models.CharField(max_length=30, choices=Kinds.choices, default=Kinds.OTHER)
    file = models.FileField(
        upload_to='business_documents/%Y/%m/', validators=[validate_pdf_document]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.file:
            try:
                validate_pdf_document(self.file)
            except ValidationError as exc:
                raise ValidationError({'file': exc.messages}) from exc

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.get_kind_display()} - {self.business.name}'
