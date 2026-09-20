from django.db import models


class LGA(models.Model):
    """Local Government Authority."""

    name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        verbose_name = 'LGA'
        verbose_name_plural = 'LGAs'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.region})'


class LicenceType(models.Model):
    """A category of business licence issued by an LGA."""

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    fee = models.DecimalField(max_digits=12, decimal_places=2)
    validity_months = models.PositiveIntegerField(default=12)
    requires_inspection = models.BooleanField(default=True)
    lga = models.ForeignKey(LGA, on_delete=models.CASCADE, related_name='licence_types')

    class Meta:
        ordering = ['lga__name', 'name']
        constraints = [
            models.UniqueConstraint(fields=['lga', 'code'], name='unique_licence_type_code_per_lga'),
        ]

    def __str__(self):
        return f'{self.name} - {self.lga.name}'


class Requirement(models.Model):
    """A document/condition required for a licence type."""

    class Kind(models.TextChoices):
        DOCUMENT = 'DOCUMENT', 'Document'
        INSPECTION = 'INSPECTION', 'Inspection'
        CLEARANCE = 'CLEARANCE', 'External clearance'

    licence_type = models.ForeignKey(LicenceType, on_delete=models.CASCADE, related_name='requirements')
    name = models.CharField(max_length=150)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.DOCUMENT)
    is_mandatory = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['licence_type', 'order', 'name']

    def __str__(self):
        return f'{self.licence_type.code}: {self.name}'


class OfficerAssignment(models.Model):
    """Assign LGA staff to handle applications of a licence type."""

    officer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='assignments')
    licence_type = models.ForeignKey(LicenceType, on_delete=models.CASCADE, related_name='assignments')
    can_review = models.BooleanField(default=True)
    can_inspect = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assigned_at']
        constraints = [
            models.UniqueConstraint(
                fields=['officer', 'licence_type'],
                condition=models.Q(is_active=True),
                name='unique_active_assignment',
            ),
        ]

    def __str__(self):
        return f'{self.officer} -> {self.licence_type}'
