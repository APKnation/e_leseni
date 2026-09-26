import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import NidaData
from lga.models import LGA, LicenceType, Ward
from businesses.models import Business, BusinessLocation
from applications.models import Application, DocumentRequirement, ApplicationDocument, StatusHistory
from licences.models import Licence

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with a full demo flow'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding demo data...")

        # 1. Users
        applicant, _ = User.objects.get_or_create(username='applicant', defaults={
            'email': 'applicant@example.com',
            'first_name': 'Demo',
            'last_name': 'Applicant',
            'role': 'APPLICANT'
        })
        applicant.set_password('Password1234!')
        applicant.save()
        
        NidaData.objects.get_or_create(
            nin='19900101123456789012',
            defaults={
                'first_name': 'Demo',
                'last_name': 'Applicant',
                'date_of_birth': '1990-01-01',
                'gender': 'M'
            }
        )
        applicant.nida_number = '19900101123456789012'
        applicant.nida_verified = True
        applicant.save()

        officer, _ = User.objects.get_or_create(username='officer', defaults={
            'role': 'LGA_OFFICER',
            'first_name': 'LGA',
            'last_name': 'Officer'
        })
        officer.set_password('Password1234!')
        officer.save()

        inspector, _ = User.objects.get_or_create(username='inspector', defaults={
            'role': 'LGA_INSPECTOR',
            'first_name': 'LGA',
            'last_name': 'Inspector'
        })
        inspector.set_password('Password1234!')
        inspector.save()

        approver, _ = User.objects.get_or_create(username='approver', defaults={
            'role': 'LGA_APPROVER',
            'first_name': 'LGA',
            'last_name': 'Approver'
        })
        approver.set_password('Password1234!')
        approver.save()

        # 2. LGA & Licence Type
        lga, _ = LGA.objects.get_or_create(name='Dar es Salaam City Council', defaults={
            'code': 'DAR01',
            'region': 'Dar es Salaam'
        })
        
        ward, _ = Ward.objects.get_or_create(lga=lga, name='Kivukoni', defaults={'code': 'KV01'})

        licence_type, _ = LicenceType.objects.get_or_create(lga=lga, name='Food Handler', defaults={
            'code': 'FH01',
            'fee': 50000.00,
            'description': 'Licence for food handling businesses'
        })

        req, _ = DocumentRequirement.objects.get_or_create(licence_type=licence_type, name='Health Certificate', defaults={
            'is_mandatory': True
        })

        # 3. Business
        business, _ = Business.objects.get_or_create(owner=applicant, name='Demo Restaurant', defaults={
            'tin_number': '123-456-789',
            'tin_verified': True,
            'brela_registration_number': 'BRELA-999',
            'brela_verified': True,
            'is_verified': True,
            'sector': 'Food & Beverage'
        })

        loc, _ = BusinessLocation.objects.get_or_create(business=business, lga=lga, defaults={
            'ward': ward,
            'street': 'Samora Ave'
        })

        # 4. Application Flow (DRAFT, SUBMITTED, INSPECTED, ISSUED)
        
        # Application 1: DRAFT
        Application.objects.get_or_create(
            business=business, 
            licence_type=licence_type, 
            lga=lga, 
            status=Application.Status.DRAFT,
            defaults={
                'applicant': applicant,
                'business_location': loc,
                'reference_number': 'APP-DRAFT-001',
            }
        )

        # Application 2: SUBMITTED
        Application.objects.get_or_create(
            business=business, 
            licence_type=licence_type, 
            lga=lga, 
            status=Application.Status.SUBMITTED,
            defaults={
                'applicant': applicant,
                'business_location': loc,
                'reference_number': 'APP-SUBMITTED-002',
                'purpose_statement': 'Demo submitted application'
            }
        )

        # Application 3: INSPECTED
        Application.objects.get_or_create(
            business=business, 
            licence_type=licence_type, 
            lga=lga, 
            status=Application.Status.INSPECTED,
            defaults={
                'applicant': applicant,
                'business_location': loc,
                'reference_number': 'APP-INSPECTED-003',
                'purpose_statement': 'Demo inspected application'
            }
        )

        # Application 4: ISSUED
        app_issued, created = Application.objects.get_or_create(
            business=business, 
            licence_type=licence_type, 
            lga=lga, 
            status=Application.Status.ISSUED,
            defaults={
                'applicant': applicant,
                'business_location': loc,
                'reference_number': 'APP-ISSUED-004',
                'purpose_statement': 'Demo issued application'
            }
        )

        if created:
            # Create a licence for the ISSUED application
            from licences.services import build_qr_payload
            licence = Licence.objects.create(
                application=app_issued,
                holder=applicant,
                licence_type=licence_type,
                lga=lga,
                business_name=business.name,
                business_tin=business.tin_number,
                licence_number='LIC-DEMO-999',
                status=Licence.Status.ACTIVE,
                valid_from=timezone.now().date(),
                valid_until=(timezone.now() + datetime.timedelta(days=365)).date()
            )
            # The signal will create a qr_token. We can re-save if needed.

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
        self.stdout.write('Users: applicant, officer, inspector, approver (password: Password1234!)')

