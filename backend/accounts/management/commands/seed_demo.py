"""
Management command: seed_demo
Creates a full demo dataset so judges can experience the entire e-Leseni flow
without needing to register anything manually.

Usage:
    python manage.py seed_demo
"""

import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from businesses.models import Business, BusinessLocation
from applications.models import Application
from lga.models import LGA, LicenceType, Requirement, Ward
from licences.models import Licence

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with a complete demo flow for judges."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding demo data…"))

        # ── 1. Users ──────────────────────────────────────────────────────────
        applicant = self._upsert_user(
            username="applicant",
            role="APPLICANT",
            first_name="Demo",
            last_name="Applicant",
            email="applicant@eleseni.demo",
            phone_number="0712000001",
            nida_number="12345678901234567890",
        )

        officer = self._upsert_user(
            username="officer",
            role="OFFICER",
            first_name="LGA",
            last_name="Officer",
            email="officer@eleseni.demo",
            phone_number="0712000002",
        )

        inspector = self._upsert_user(
            username="inspector",
            role="INSPECTOR",
            first_name="LGA",
            last_name="Inspector",
            email="inspector@eleseni.demo",
            phone_number="0712000003",
        )

        approver = self._upsert_user(
            username="approver",
            role="APPROVER",
            first_name="LGA",
            last_name="Approver",
            email="approver@eleseni.demo",
            phone_number="0712000004",
        )

        admin = self._upsert_user(
            username="admin",
            role="ADMIN",
            first_name="System",
            last_name="Admin",
            email="admin@eleseni.demo",
            phone_number="0712000005",
            is_staff=True,
            is_superuser=True,
        )

        # ── 2. LGA ────────────────────────────────────────────────────────────
        lga, _ = LGA.objects.get_or_create(
            code="DSM01",
            defaults={
                "name": "Dar es Salaam City Council",
                "region": "Dar es Salaam",
                "tier": LGA.Tier.CITY,
            },
        )

        # Assign LGA staff to this LGA
        for staff_user in [officer, inspector, approver, admin]:
            staff_user.lga = lga
            staff_user.save(update_fields=["lga"])

        ward, _ = Ward.objects.get_or_create(
            lga=lga,
            name="Kivukoni",
        )

        # ── 3. Licence Types ──────────────────────────────────────────────────
        food_handler, _ = LicenceType.objects.get_or_create(
            lga=lga,
            code="FH01",
            defaults={
                "name": "Food Handler",
                "category": LicenceType.Category.BUSINESS,
                "description": "Licence required for all food handling and preparation businesses.",
                "fee": 50000.00,
                "validity_months": 12,
                "requires_inspection": True,
            },
        )

        general_trade, _ = LicenceType.objects.get_or_create(
            lga=lga,
            code="GT01",
            defaults={
                "name": "General Trade",
                "category": LicenceType.Category.BUSINESS,
                "description": "General business trading licence.",
                "fee": 30000.00,
                "validity_months": 12,
                "requires_inspection": False,
            },
        )

        # Document requirements for Food Handler
        Requirement.objects.get_or_create(
            licence_type=food_handler,
            name="Health Certificate",
            defaults={"is_mandatory": True, "kind": "DOCUMENT", "order": 1},
        )
        Requirement.objects.get_or_create(
            licence_type=food_handler,
            name="Premises Certificate",
            defaults={"is_mandatory": True, "kind": "DOCUMENT", "order": 2},
        )

        # ── 4. Business ───────────────────────────────────────────────────────
        business, _ = Business.objects.get_or_create(
            owner=applicant,
            name="Demo Restaurant & Catering",
            defaults={
                "tin_number": "123-456-789",
                "brela_registration_number": "BRELA-DEMO-9999",
                "nida_number": applicant.nida_number,
                "sector": "Food & Beverage",
                "is_verified": True,
            },
        )

        location, _ = BusinessLocation.objects.get_or_create(
            business=business,
            lga=lga,
            defaults={
                "ward": ward.name,
                "street": "Samora Avenue",
                "plot_number": "17",
                "is_primary": True,
            },
        )

        # ── 5. Applications at each stage ─────────────────────────────────────
        # 5a. DRAFT
        self._get_or_create_application(
            applicant=applicant,
            business=business,
            location=location,
            licence_type=food_handler,
            status=Application.Status.DRAFT,
            purpose_statement="New restaurant at Samora Avenue — draft.",
        )

        # 5b. SUBMITTED
        self._get_or_create_application(
            applicant=applicant,
            business=business,
            location=location,
            licence_type=food_handler,
            status=Application.Status.SUBMITTED,
            purpose_statement="Takeaway food outlet — awaiting officer review.",
        )

        # 5c. UNDER_REVIEW
        self._get_or_create_application(
            applicant=applicant,
            business=business,
            location=location,
            licence_type=general_trade,
            status=Application.Status.UNDER_REVIEW,
            purpose_statement="General merchandise — under officer review.",
        )

        # 5d. INSPECTED
        self._get_or_create_application(
            applicant=applicant,
            business=business,
            location=location,
            licence_type=general_trade,
            status=Application.Status.INSPECTED,
            purpose_statement="Passed site inspection — awaiting approver decision.",
        )

        # 5e. ISSUED — create application + licence (with scannable QR)
        app_issued, created = Application.objects.get_or_create(
            business=business,
            licence_type=food_handler,
            status=Application.Status.ISSUED,
            defaults={
                "applicant": applicant,
                "location": location,
                "purpose_statement": "Licence already issued — demo the QR code scan.",
            },
        )

        if not Licence.objects.filter(application=app_issued).exists():
            Licence.objects.create(
                application=app_issued,
                holder=applicant,
                licence_type=food_handler,
                lga=lga,
                business_name=business.name,
                status=Licence.Status.ACTIVE,
                valid_from=timezone.now().date(),
                valid_until=(timezone.now() + datetime.timedelta(days=365)).date(),
            )
            self.stdout.write("  Created issued licence with QR token.")

        # ── Done ──────────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("\n✅  Demo seed complete!\n"))
        self.stdout.write("Demo accounts (password: Password1234!):")
        self.stdout.write("  applicant  — APPLICANT role")
        self.stdout.write("  officer    — LGA Officer (can review)")
        self.stdout.write("  inspector  — LGA Inspector (can conduct inspections)")
        self.stdout.write("  approver   — LGA Approver (can approve/issue)")
        self.stdout.write("  admin      — System Admin (full access)\n")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _upsert_user(self, username, role, **kwargs):
        is_staff = kwargs.pop("is_staff", False)
        is_superuser = kwargs.pop("is_superuser", False)
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"role": role, "is_staff": is_staff, "is_superuser": is_superuser, **kwargs},
        )
        if created:
            user.set_password("Password1234!")
            user.save()
            self.stdout.write(f"  Created user: {username}")
        else:
            self.stdout.write(f"  Existing user: {username}")
        return user

    def _get_or_create_application(self, *, applicant, business, location, licence_type, status, purpose_statement):
        app, created = Application.objects.get_or_create(
            business=business,
            licence_type=licence_type,
            status=status,
            defaults={
                "applicant": applicant,
                "location": location,
                "purpose_statement": purpose_statement,
            },
        )
        label = "Created" if created else "Existing"
        self.stdout.write(f"  {label} application: {status}")
        return app
