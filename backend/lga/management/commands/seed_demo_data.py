"""Seed demo data for local development and testing.

Usage:
    python manage.py seed_demo_data            # create anything missing
    python manage.py seed_demo_data --reset    # delete demo data first, then reseed

Creates: LGAs, licence types (+ requirements), users with roles, officer
assignments, businesses with locations, and one submitted demo application.
Idempotent: safe to run repeatedly; existing rows are updated, not duplicated.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from applications.models import Application
from businesses.models import Business, BusinessLocation
from lga.models import LGA, LicenceType, OfficerAssignment, Requirement
from lga.tanzania_lgas import TANZANIA_LGAS, lga_code

User = get_user_model()

DEMO_PASSWORD = 'Demo@1234'

# Detailed LGAs kept for the demo application fixtures below.
KEY_LGAS = [
    {'name': 'Ilala', 'region': 'Dar es Salaam', 'code': 'DS-ILALA'},
    {'name': 'Kinondoni', 'region': 'Dar es Salaam', 'code': 'DS-KINONDONI'},
    {'name': 'Temeke', 'region': 'Dar es Salaam', 'code': 'DS-TEMEKE'},
    {'name': 'Moshi Municipal', 'region': 'Kilimanjaro', 'code': 'KI-MOSHI_MUNICIPAL'},
]

# Standard licences created for EVERY LGA so area-based selection always works.
STANDARD_LICENCES = [
    {
        'name': 'Business Licence',
        'category': LicenceType.Category.BUSINESS,
        'fee': Decimal('50000'),
        'validity_months': 12,
        'requires_inspection': True,
        'description': 'General licence to operate a business within this council.',
        'requirements': [
            {'name': 'TIN Certificate', 'kind': Requirement.Kind.DOCUMENT},
            {'name': 'BRELA Registration', 'kind': Requirement.Kind.DOCUMENT},
            {'name': 'Premises Inspection', 'kind': Requirement.Kind.INSPECTION},
        ],
    },
    {
        'name': 'Food Vendor Licence',
        'category': LicenceType.Category.BUSINESS,
        'fee': Decimal('30000'),
        'validity_months': 12,
        'requires_inspection': True,
        'description': 'For food stalls, restaurants and catering businesses.',
        'requirements': [
            {'name': 'Food Handling Permit', 'kind': Requirement.Kind.DOCUMENT},
            {'name': 'Premises Inspection', 'kind': Requirement.Kind.INSPECTION},
        ],
    },
    {
        'name': 'Driving Licence Renewal',
        'category': LicenceType.Category.DRIVING,
        'fee': Decimal('70000'),
        'validity_months': 36,
        'requires_inspection': False,
        'description': 'Renewal of a national driving licence processed at council level.',
        'requirements': [
            {'name': 'Existing Driving Licence', 'kind': Requirement.Kind.DOCUMENT},
            {'name': 'TRA Clearance', 'kind': Requirement.Kind.CLEARANCE},
        ],
    },
    {
        'name': 'New Driving Licence',
        'category': LicenceType.Category.DRIVING,
        'fee': Decimal('120000'),
        'validity_months': 36,
        'requires_inspection': False,
        'description': 'First-time driving licence issued after passing the TRA/Traffic test.',
        'requirements': [
            {'name': 'Traffic Test Certificate', 'kind': Requirement.Kind.CLEARANCE},
            {'name': 'ID/Passport Copy', 'kind': Requirement.Kind.DOCUMENT},
        ],
    },
]

LICENCE_TYPES = [
    {
        'lga_code': 'DS-ILALA',
        'name': 'Food Vendor Licence',
        'code': 'FOOD-ILALA',
        'fee': Decimal('50000'),
        'validity_months': 12,
        'requires_inspection': True,
        'description': 'For restaurants, food stalls and catering businesses in Ilala.',
        'requirements': [
            {'name': 'TIN Certificate', 'kind': Requirement.Kind.DOCUMENT},
            {'name': 'Food Handling Permit', 'kind': Requirement.Kind.DOCUMENT},
            {'name': 'Premises Inspection', 'kind': Requirement.Kind.INSPECTION},
        ],
    },
    {
        'lga_code': 'DS-ILALA',
        'name': 'Retail Shop Licence',
        'code': 'RETAIL-ILALA',
        'fee': Decimal('120000'),
        'validity_months': 12,
        'requires_inspection': True,
        'description': 'For retail and wholesale shops in Ilala.',
        'requirements': [
            {'name': 'TIN Certificate', 'kind': Requirement.Kind.DOCUMENT},
            {'name': 'Lease Agreement', 'kind': Requirement.Kind.DOCUMENT},
        ],
    },
    {
        'lga_code': 'DS-KINONDONI',
        'name': 'Hardware Shop Licence',
        'code': 'HW-KINONDONI',
        'fee': Decimal('80000'),
        'validity_months': 12,
        'requires_inspection': False,
        'description': 'For hardware and building-material vendors in Kinondoni.',
        'requirements': [
            {'name': 'TIN Certificate', 'kind': Requirement.Kind.DOCUMENT},
        ],
    },
    {
        'lga_code': 'KI-MOSHI_MUNICIPAL',
        'name': 'Kiosk Licence',
        'code': 'KIOSK-MOSHI',
        'fee': Decimal('30000'),
        'validity_months': 12,
        'requires_inspection': False,
        'description': 'For small kiosks and street-side vendors in Moshi.',
        'requirements': [],
    },
]

USERS = [
    {
        'username': 'admin',
        'first_name': 'System', 'last_name': 'Admin',
        'email': 'admin@leseni.local', 'phone_number': '0700000001',
        'role': User.Roles.ADMIN, 'is_staff': True, 'is_superuser': True,
        'lga': 'DS-ILALA',
    },
    {
        'username': 'officer1',
        'first_name': 'Amina', 'last_name': 'Juma',
        'email': 'officer1@leseni.local', 'phone_number': '0700000002',
        'role': User.Roles.OFFICER, 'is_staff': True, 'is_superuser': False,
        'lga': 'DS-ILALA',
    },
    {
        'username': 'inspector1',
        'first_name': 'Baraka', 'last_name': 'Mushi',
        'email': 'inspector1@leseni.local', 'phone_number': '0700000003',
        'role': User.Roles.INSPECTOR, 'is_staff': True, 'is_superuser': False,
        'lga': 'DS-ILALA',
    },
    {
        'username': 'applicant1',
        'first_name': 'Neema', 'last_name': 'Robert',
        'email': 'applicant1@leseni.local', 'phone_number': '0712000111',
        'role': User.Roles.APPLICANT, 'is_staff': False, 'is_superuser': False,
        'lga': None,
    },
    {
        'username': 'applicant2',
        'first_name': 'Joseph', 'last_name': 'Komba',
        'email': 'applicant2@leseni.local', 'phone_number': '0712000222',
        'role': User.Roles.APPLICANT, 'is_staff': False, 'is_superuser': False,
        'lga': None,
    },
]

BUSINESSES = [
    {
        'owner': 'applicant1',
        'name': 'Mama Neema Foods',
        'tin_number': '123456789',
        'brela_registration_number': '100987654',
        'sector': 'Food & Beverage',
        'lga': 'DS-ILALA', 'ward': 'Upanga', 'street': 'Ocean Road', 'plot_number': '12',
    },
    {
        'owner': 'applicant2',
        'name': 'Komba Hardware',
        'tin_number': '987654321',
        'brela_registration_number': '102345678',
        'sector': 'Retail',
        'lga': 'KI-MOSHI_MUNICIPAL', 'ward': 'Pasua', 'street': 'Old Moshi Road', 'plot_number': '45',
    },
]


class Command(BaseCommand):
    help = 'Seed demo LGAs, licence types, users, businesses and a demo application.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Delete previously seeded demo rows first (identifies them by fixed usernames/codes).',
        )

    # -- helpers -----------------------------------------------------------

    def _stdout(self, msg):
        self.stdout.write(msg)

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            self._reset()

        self._seed_lgas()
        self._seed_standard_licences()
        self._seed_demo_licences()
        self._seed_users()
        self._seed_assignments()
        self._seed_businesses()
        self._seed_demo_application()

        self._stdout(self.style.SUCCESS(
            f'Done. LGAs: {LGA.objects.count()}, licence types: {LicenceType.objects.count()}. '
            f'Demo accounts (password: {DEMO_PASSWORD}):'
        ))
        for u in USERS:
            self._stdout(f'  - {u["username"]:12s} {u["role"]:10s} staff={u["is_staff"]}')

    # -- sections ----------------------------------------------------------

    def _reset(self):
        deleted = 0
        for model, lookup in (
            (Application, {'applicant__username__in': [u['username'] for u in USERS]}),
            (Business, {'owner__username__in': [u['username'] for u in USERS]}),
            (User, {'username__in': [u['username'] for u in USERS]}),
            (OfficerAssignment, {}),
            (Requirement, {}),
            (LicenceType, {}),
            (LGA, {}),
        ):
            count, _ = model.objects.filter(**lookup).delete()
            deleted += count
        self._stdout(f'Reset: deleted {deleted} rows.')

    def _seed_lgas(self):
        created_count = 0
        for region, names in TANZANIA_LGAS.items():
            for name in names:
                code = lga_code(region, name)
                _, created = LGA.objects.update_or_create(
                    code=code,
                    defaults={'name': name, 'region': region},
                )
                created_count += 1 if created else 0
        self._stdout(f'  + LGAs: {LGA.objects.count()} total across {len(TANZANIA_LGAS)} regions.')

    def _seed_standard_licences(self):
        """Create the standard licences for every LGA (area-based selection)."""
        created_count = 0
        lgas = LGA.objects.all()
        for lga in lgas:
            for spec in STANDARD_LICENCES:
                code = f'{lga.code}-BUS' if spec['category'] == LicenceType.Category.BUSINESS and spec['name'] == 'Business Licence' else None
                if code is None:
                    # Deterministic per-LGA code from the licence name.
                    slug = spec['name'].upper().replace(' ', '_')[:20]
                    code = f'{lga.code}-{slug}'
                lt, created = self._upsert_licence(lga, code, spec)
                created_count += 1 if created else 0
        self._stdout(f'  + Standard licences: {created_count} created for {lgas.count()} LGAs.')

    def _seed_demo_licences(self):
        """Richer demo licence types for the key LGAs (codes FOOD/RETAIL/HW/KIOSK kept)."""
        for spec in LICENCE_TYPES:
            lga = LGA.objects.get(code=spec['lga_code'])
            # Skip if a standard licence with the same name already covers this LGA.
            if LicenceType.objects.filter(lga=lga, name=spec['name']).exclude(code=spec['code']).exists():
                self._stdout(f'  = {spec["name"]} in {lga.name} already covered by a standard licence.')
                continue
            lt, created = self._upsert_licence(lga, spec['code'], spec)
            self._log(lt, created)

    def _upsert_licence(self, lga, code, spec):
        lt, created = LicenceType.objects.update_or_create(
            code=code,
            defaults={
                'name': spec['name'],
                'category': spec.get('category', LicenceType.Category.BUSINESS),
                'fee': spec['fee'],
                'validity_months': spec['validity_months'],
                'requires_inspection': spec['requires_inspection'],
                'description': spec['description'],
                'lga': lga,
            },
        )
        for order, req in enumerate(spec.get('requirements', []), start=1):
            Requirement.objects.update_or_create(
                licence_type=lt, name=req['name'],
                defaults={'kind': req['kind'], 'is_mandatory': True, 'order': order},
            )
        return lt, created

    def _seed_users(self):
        for spec in USERS:
            lga = LGA.objects.filter(code=spec['lga']).first() if spec['lga'] else None
            user, created = User.objects.get_or_create(
                username=spec['username'],
                defaults={
                    'first_name': spec['first_name'],
                    'last_name': spec['last_name'],
                    'email': spec['email'],
                    'phone_number': spec['phone_number'],
                    'role': spec['role'],
                    'is_staff': spec['is_staff'],
                    'is_superuser': spec['is_superuser'],
                    'lga': lga,
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=['password'])
            self._log(user, created)

    def _seed_assignments(self):
        pairs = [
            ('officer1', 'Food Vendor Licence', True, False, True),
            ('officer1', 'Retail Shop Licence', True, False, True),
            ('inspector1', 'Food Vendor Licence', False, True, False),
        ]
        ilala = LGA.objects.get(code='DS-ILALA')
        for username, licence_name, review, inspect, approve in pairs:
            officer = User.objects.get(username=username)
            licence_type = LicenceType.objects.get(lga=ilala, name=licence_name)
            assignment, created = OfficerAssignment.objects.update_or_create(
                officer=officer, licence_type=licence_type,
                defaults={
                    'can_review': review, 'can_inspect': inspect,
                    'can_approve': approve, 'is_active': True,
                },
            )
            self._log(assignment, created)

    def _seed_businesses(self):
        for spec in BUSINESSES:
            owner = User.objects.get(username=spec['owner'])
            business, created = Business.objects.get_or_create(
                owner=owner, name=spec['name'],
                defaults={
                    'tin_number': spec['tin_number'],
                    'brela_registration_number': spec['brela_registration_number'],
                    'sector': spec['sector'],
                    'is_verified': False,
                },
            )
            if created:
                BusinessLocation.objects.create(
                    business=business,
                    lga=LGA.objects.get(code=spec['lga']),
                    ward=spec['ward'], street=spec['street'],
                    plot_number=spec['plot_number'], is_primary=True,
                )
            self._log(business, created)

    def _seed_demo_application(self):
        """One submitted application so the dashboard/staff queue are not empty."""
        applicant = User.objects.get(username='applicant1')
        business = Business.objects.get(owner=applicant, name='Mama Neema Foods')
        ilala = LGA.objects.get(code='DS-ILALA')
        licence_type = LicenceType.objects.get(lga=ilala, name='Food Vendor Licence')
        location = BusinessLocation.objects.get(business=business)

        if Application.objects.filter(applicant=applicant, licence_type=licence_type).exists():
            self._stdout('  = Demo application already exists, skipping.')
            return

        application = Application.objects.create(
            applicant=applicant, business=business,
            licence_type=licence_type, location=location,
            purpose_statement='Selling grilled chicken and beverages near the market.',
        )
        application.transition_to(Application.Status.SUBMITTED, by=applicant)
        self._stdout(f'  + Demo application {application.reference_number} submitted.')

    def _log(self, obj, created):
        verb = '+' if created else '='
        self._stdout(f'  {verb} {obj}')
