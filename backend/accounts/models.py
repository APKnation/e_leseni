import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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


class PasswordResetToken(models.Model):
    """Short-lived token for password reset via phone or email lookup."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    TOKEN_EXPIRY_MINUTES = 30

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'ResetToken({self.user.username}, used={self.used})'

    @classmethod
    def generate_for(cls, user):
        """Invalidate old tokens and issue a fresh one."""
        cls.objects.filter(user=user, used=False).delete()
        return cls.objects.create(
            user=user,
            token=secrets.token_urlsafe(32),
        )

    @property
    def is_valid(self):
        if self.used:
            return False
        expiry = self.created_at + timedelta(minutes=self.TOKEN_EXPIRY_MINUTES)
        return timezone.now() < expiry
