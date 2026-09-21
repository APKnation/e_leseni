from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with LGA licensing roles."""

    class Roles(models.TextChoices):
        APPLICANT = 'APPLICANT', 'Applicant'
        OFFICER = 'OFFICER', 'Licensing Officer'
        INSPECTOR = 'INSPECTOR', 'Inspector'
        APPROVER = 'APPROVER', 'Approver'
        ADMIN = 'ADMIN', 'System Admin'

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.APPLICANT)
    phone_number = models.CharField(max_length=15, blank=True)
    nida_number = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text='National Identification Number (NIDA), 20 digits, verified via integrations app.',
    )
    lga = models.ForeignKey(
        'lga.LGA',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='staff',
        help_text='LGA the user belongs to (required for officers/inspectors).',
    )

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_lga_staff(self):
        return self.role in {
            self.Roles.OFFICER,
            self.Roles.INSPECTOR,
            self.Roles.APPROVER,
            self.Roles.ADMIN,
        }
