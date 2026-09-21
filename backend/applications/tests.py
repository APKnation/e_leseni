from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from applications.models import Application
from businesses.models import Business, BusinessLocation
from lga.models import LGA, LicenceType


class ApplicationStatusFlowTests(TestCase):
    """State-machine unit tests for transition_to()."""

    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.applicant = User.objects.create_user(
            username='applicant1', password='testpass123', nida_number='7' * 20
        )
        self.lga = LGA.objects.create(name='Ilala', region='Dar es Salaam', code='DS-ILALA')
        self.licence_type = LicenceType.objects.create(
            name='Food Vendor Licence', code='FOOD', fee=50000, lga=self.lga
        )
        self.business = Business.objects.create(name='Mama Ntilie Foods', owner=self.applicant)
        self.location = BusinessLocation.objects.create(
            business=self.business, lga=self.lga, ward='Upanga', street='Ocean Road'
        )
        self.application = Application.objects.create(
            applicant=self.applicant,
            business=self.business,
            licence_type=self.licence_type,
            location=self.location,
        )

    def test_reference_number_generated(self):
        self.assertTrue(self.application.reference_number.startswith('EL-FOOD-'))

    def test_happy_path_to_issued(self):
        app = self.application
        for status_ in ('SUBMITTED', 'UNDER_REVIEW', 'INSPECTION_SCHEDULED', 'INSPECTED',
                        'APPROVED', 'PAYMENT_PENDING', 'PAID', 'ISSUED'):
            app.transition_to(status_)
            self.assertEqual(app.status, status_)

    def test_invalid_transition_rejected(self):
        with self.assertRaises(ValueError):
            self.application.transition_to('APPROVED')

    def test_returned_for_correction_loop(self):
        app = self.application
        app.transition_to('SUBMITTED')
        app.transition_to('UNDER_REVIEW')
        app.transition_to('RETURNED_FOR_CORRECTION')
        app.transition_to('DRAFT')
        app.transition_to('SUBMITTED')
        self.assertEqual(app.status, 'SUBMITTED')

    def test_rejection_branch_is_terminal(self):
        app = self.application
        app.transition_to('SUBMITTED')
        app.transition_to('UNDER_REVIEW')
        app.transition_to('REJECTED', note='Missing TIN certificate')
        self.assertEqual(app.rejection_reason, 'Missing TIN certificate')
        with self.assertRaises(ValueError):
            app.transition_to('DRAFT')


class MultipleApplicationsAPITests(APITestCase):
    """An applicant may hold many licences and register many businesses."""

    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.applicant = User.objects.create_user(
            username='multi1', password='testpass123', phone_number='0755000111',
            nida_number='1' * 20,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.applicant)

        self.lga = LGA.objects.create(name='Ilala', region='Dar es Salaam', code='DS-ILALA')
        self.licence_a = LicenceType.objects.create(
            name='Business Licence', code='BIZ-A', fee=50000, lga=self.lga
        )
        self.licence_b = LicenceType.objects.create(
            name='New Driving Licence', code='DRV-A', fee=120000, lga=self.lga,
            requires_inspection=False,
        )
        self.business = Business.objects.create(
            owner=self.applicant, name='Komba Hardware',
            tin_number='987654321', brela_registration_number='102345678',
        )
        self.location = BusinessLocation.objects.create(
            business=self.business, lga=self.lga, ward='Pasua',
            street='Old Moshi Road', is_primary=True,
        )

    def _create_application(self, business, licence, location):
        payload = {
            'business': business.id,
            'licence_type': licence.id,
            'location': location.id,
            'purpose_statement': 'Test purpose',
        }
        response = self.client.post('/api/applications/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data

    def test_second_application_different_licence_same_business(self):
        """One business may hold several concurrent applications."""
        first = self._create_application(self.business, self.licence_a, self.location)
        second = self._create_application(self.business, self.licence_b, self.location)

        self.assertNotEqual(first['id'], second['id'])
        self.assertNotEqual(first['reference_number'], second['reference_number'])
        self.assertEqual(Application.objects.filter(business=self.business).count(), 2)

    def test_same_licence_twice_is_allowed(self):
        """E.g. the same licence for two branches of one business."""
        first = self._create_application(self.business, self.licence_a, self.location)
        second = self._create_application(self.business, self.licence_a, self.location)
        self.assertNotEqual(first['id'], second['id'])

    def test_new_business_then_licence_for_another_activity(self):
        """The 'register another activity' journey end-to-end via the API."""
        # Register a second business
        response = self.client.post(
            '/api/businesses/',
            {'name': 'Komba Salon', 'tin_number': '123456789',
             'brela_registration_number': '100987654', 'sector': 'Services'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        salon = Business.objects.get(owner=self.applicant, name='Komba Salon')

        # Add its location
        response = self.client.post(
            '/api/business-locations/',
            {'business': salon.id, 'lga': self.lga.id, 'ward': 'Kariakoo',
             'street': 'Ocean Road', 'is_primary': True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        location = BusinessLocation.objects.get(business=salon, ward='Kariakoo')

        # Apply for a licence for the new activity
        application = self._create_application(salon, self.licence_a, location)
        self.assertEqual(application['business_name'], 'Komba Salon')
        self.assertEqual(application['status'], 'DRAFT')
        self.assertTrue(application['reference_number'].startswith('EL-BIZ-A'))

        # Applicant now has both businesses and the new application
        self.assertEqual(Business.objects.filter(owner=self.applicant).count(), 2)
        self.assertEqual(Application.objects.filter(applicant=self.applicant).count(), 1)
        self.assertEqual(Application.objects.get(pk=application['id']).business_id, salon.id)

    def test_applicant_sees_only_own_applications(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other = User.objects.create_user(username='other2', password='testpass123', nida_number='6' * 20)

        self._create_application(self.business, self.licence_a, self.location)

        response = self.client.get('/api/applications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        self.client.force_authenticate(user=other)
        response = self.client.get('/api/applications/')
        self.assertEqual(response.data['count'], 0)


class BusinessRegistrationRulesTests(APITestCase):
    """The only restriction: an owner can't register the same business name twice."""

    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.user = User.objects.create_user(username='dup1', password='testpass123', nida_number='2' * 20)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_duplicate_name_for_same_owner_blocked(self):
        Business.objects.create(owner=self.user, name='Same Name Ltd')
        response = self.client.post('/api/businesses/', {'name': 'Same Name Ltd'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_name_different_owners_ok(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other = User.objects.create_user(username='dup2', password='testpass123', nida_number='3' * 20)
        Business.objects.create(owner=other, name='Kariakoo Traders')

        response = self.client.post('/api/businesses/', {'name': 'Kariakoo Traders'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class RoleWorkflowAPITests(APITestCase):
    """Each staff role may only perform its own transitions on its own LGA."""

    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.applicant = User.objects.create_user(
            username='roleapplicant', password='testpass123', phone_number='0755000111',
            nida_number='4' * 20,
        )
        self.lga_a = LGA.objects.create(name='Ilala', region='Dar es Salaam', code='DS-ILALA')
        self.lga_b = LGA.objects.create(name='Moshi Municipal', region='Kilimanjaro', code='KI-MOSHI')
        self.licence_a = LicenceType.objects.create(
            name='Food Vendor Licence', code='FOOD-A', fee=50000, lga=self.lga_a
        )
        self.licence_b = LicenceType.objects.create(
            name='Kiosk Licence', code='KIOSK-B', fee=30000, lga=self.lga_b
        )
        self.business = Business.objects.create(
            owner=self.applicant, name='Role Test Foods',
            tin_number='123456789', brela_registration_number='102345678',
        )
        self.location_a = BusinessLocation.objects.create(
            business=self.business, lga=self.lga_a, ward='Upanga',
            street='Ocean Road', is_primary=True,
        )
        self.location_b = BusinessLocation.objects.create(
            business=self.business, lga=self.lga_b, ward='Pasua', street='Old Moshi Road',
        )

        self.officer = User.objects.create_user(
            username='roleofficer', password='testpass123', role='OFFICER', lga=self.lga_a
        )
        self.inspector = User.objects.create_user(
            username='roleinspector', password='testpass123', role='INSPECTOR', lga=self.lga_a
        )
        self.approver = User.objects.create_user(
            username='roleapprover', password='testpass123', role='APPROVER', lga=self.lga_a
        )
        self.admin = User.objects.create_user(
            username='roleadmin', password='testpass123', role='ADMIN', lga=self.lga_a
        )
        self.other_officer = User.objects.create_user(
            username='roleofficer_b', password='testpass123', role='OFFICER', lga=self.lga_b
        )

    def _application(self, licence_type, location):
        return Application.objects.create(
            applicant=self.applicant,
            business=self.business,
            licence_type=licence_type,
            location=location,
            status=Application.Status.SUBMITTED,
            submitted_at='2026-01-01T00:00:00Z',
        )

    def _transition(self, user, application, to_status):
        self.client.force_authenticate(user=user)
        return self.client.post(
            f'/api/applications/{application.id}/transition/',
            {'to_status': to_status}, format='json',
        )

    def test_officer_can_start_review(self):
        app = self._application(self.licence_a, self.location_a)
        response = self._transition(self.officer, app, 'UNDER_REVIEW')
        self.assertEqual(response.status_code, 200, response.data)
        app.refresh_from_db()
        self.assertEqual(app.status, 'UNDER_REVIEW')
        self.assertEqual(app.assigned_officer, self.officer)

    def test_officer_cannot_approve(self):
        app = self._application(self.licence_a, self.location_a)
        app.transition_to('UNDER_REVIEW', by=self.officer)
        app.transition_to('INSPECTION_SCHEDULED', by=self.officer)
        app.transition_to('INSPECTED', by=self.inspector)
        response = self._transition(self.officer, app, 'APPROVED')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inspector_cannot_start_review(self):
        app = self._application(self.licence_a, self.location_a)
        response = self._transition(self.inspector, app, 'UNDER_REVIEW')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inspector_can_mark_inspected(self):
        app = self._application(self.licence_a, self.location_a)
        app.transition_to('UNDER_REVIEW', by=self.officer)
        app.transition_to('INSPECTION_SCHEDULED', by=self.officer)
        response = self._transition(self.inspector, app, 'INSPECTED')
        self.assertEqual(response.status_code, 200, response.data)

    def test_approver_cannot_start_review_but_can_approve(self):
        app = self._application(self.licence_a, self.location_a)
        response = self._transition(self.approver, app, 'UNDER_REVIEW')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        app.transition_to('UNDER_REVIEW', by=self.officer)
        app.transition_to('INSPECTION_SCHEDULED', by=self.officer)
        app.transition_to('INSPECTED', by=self.inspector)
        response = self._transition(self.approver, app, 'APPROVED')
        self.assertEqual(response.status_code, 200, response.data)

    def test_admin_can_do_anything(self):
        app = self._application(self.licence_a, self.location_a)
        response = self._transition(self.admin, app, 'UNDER_REVIEW')
        self.assertEqual(response.status_code, 200)

    def test_officer_cannot_transition_other_lga_application(self):
        app = self._application(self.licence_b, self.location_b)
        response = self._transition(self.officer, app, 'UNDER_REVIEW')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_sees_other_lga_applications(self):
        app = self._application(self.licence_b, self.location_b)
        response = self._transition(self.admin, app, 'UNDER_REVIEW')
        self.assertEqual(response.status_code, 200)

    def test_staff_queryset_scoped_to_own_lga(self):
        self._application(self.licence_a, self.location_a)
        self._application(self.licence_b, self.location_b)

        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/applications/')
        self.assertEqual(response.data['count'], 1)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/applications/')
        self.assertEqual(response.data['count'], 2)

    def test_allowed_next_statuses_reflect_role(self):
        """The serializer only advertises transitions the current role may take."""
        app = self._application(self.licence_a, self.location_a)

        self.client.force_authenticate(user=self.officer)
        response = self.client.get('/api/applications/')
        row = next(r for r in response.data['results'] if r['id'] == app.id)
        self.assertIn('UNDER_REVIEW', row['allowed_next_statuses'])
        self.assertNotIn('APPROVED', row['allowed_next_statuses'])

        # A draft application offers its owner exactly one action: submit it.
        draft = Application.objects.create(
            applicant=self.applicant,
            business=self.business,
            licence_type=self.licence_a,
            location=self.location_a,
        )
        self.client.force_authenticate(user=self.applicant)
        response = self.client.get('/api/applications/')
        row = next(r for r in response.data['results'] if r['id'] == draft.id)
        self.assertEqual(row['allowed_next_statuses'], ['SUBMITTED'])

    def test_applicant_cannot_review_own_application(self):
        app = self._application(self.licence_a, self.location_a)
        response = self._transition(self.applicant, app, 'UNDER_REVIEW')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inspector_lists_inscriptions_scoped_to_lga(self):
        """Regression: non-admin staff can list inspections without FieldError.

        The Inspection queryset filters through application__licence_type,
        which previously crashed with 'Cannot resolve keyword licence_type'.
        """
        from applications.models import Inspection
        from django.utils import timezone

        app = self._application(self.licence_a, self.location_a)
        Inspection.objects.create(
            application=app, inspector=self.inspector, scheduled_for=timezone.now()
        )

        self.client.force_authenticate(user=self.inspector)
        response = self.client.get('/api/inspections/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        # Inspector belongs to lga_a; the Moshi application must stay hidden.
        app_b = self._application(self.licence_b, self.location_b)
        Inspection.objects.create(
            application=app_b, inspector=self.inspector, scheduled_for=timezone.now()
        )
        response = self.client.get('/api/inspections/')
        self.assertEqual(response.data['count'], 1)

        # Admin sees both.
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/inspections/')
        self.assertEqual(response.data['count'], 2)

    def test_officer_schedules_inspection_via_api(self):
        """Officers can create an inspection record for their LGA."""
        app = self._application(self.licence_a, self.location_a)
        self.client.force_authenticate(user=self.officer)
        response = self.client.post(
            '/api/inspections/',
            {'application': app.id, 'scheduled_for': '2026-10-01T09:00:00Z'},
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['inspector'], self.officer.id)


class DocumentUploadTests(APITestCase):
    """Requirement-driven document uploads gate submission."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        from lga.models import Requirement

        self.Requirement = Requirement
        User = get_user_model()
        self.applicant = User.objects.create_user(
            username='docapplicant', password='testpass123', nida_number='5' * 20
        )
        self.officer = User.objects.create_user(
            username='docofficer', password='testpass123', role='OFFICER', lga_id=None
        )
        self.lga = LGA.objects.create(name='Ilala', region='Dar es Salaam', code='DS-ILALA')
        self.officer.lga = self.lga
        self.officer.save(update_fields=['lga'])
        self.licence_type = LicenceType.objects.create(
            name='Food Vendor Licence', code='FOOD-DOC', fee=50000, lga=self.lga
        )
        self.tin_req = Requirement.objects.create(
            licence_type=self.licence_type, name='TIN Certificate',
            kind=Requirement.Kind.DOCUMENT, is_mandatory=True,
        )
        self.lease_req = Requirement.objects.create(
            licence_type=self.licence_type, name='Lease Agreement',
            kind=Requirement.Kind.DOCUMENT, is_mandatory=False,
        )
        self.business = Business.objects.create(owner=self.applicant, name='Doc Test Foods')
        self.location = BusinessLocation.objects.create(
            business=self.business, lga=self.lga, ward='Upanga', street='Ocean Road'
        )
        self.application = Application.objects.create(
            applicant=self.applicant,
            business=self.business,
            licence_type=self.licence_type,
            location=self.location,
        )
        self.client = APIClient()

    def _upload(self, requirement=None, filename='tin.pdf'):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_authenticate(user=self.applicant)
        data = {'file': SimpleUploadedFile(filename, b'%PDF-1.4 fake', content_type='application/pdf')}
        if requirement is not None:
            data['requirement'] = requirement.id
        return self.client.post(
            f'/api/applications/{self.application.id}/upload_document/', data, format='multipart'
        )

    def test_upload_document_to_draft(self):
        response = self._upload(requirement=self.tin_req)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['requirement_name'], 'TIN Certificate')
        self.assertTrue(self.application.documents.filter(requirement=self.tin_req).exists())

    def test_upload_rejects_requirement_from_other_licence(self):
        other_licence = LicenceType.objects.create(
            name='Kiosk Licence', code='KIOSK-DOC', fee=30000, lga=self.lga
        )
        other_req = self.Requirement.objects.create(
            licence_type=other_licence, name='Other Cert', kind=self.Requirement.Kind.DOCUMENT
        )
        response = self._upload(requirement=other_req)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_blocked_until_mandatory_documents_uploaded(self):
        self.client.force_authenticate(user=self.applicant)
        response = self.client.post(
            f'/api/applications/{self.application.id}/transition/',
            {'to_status': 'SUBMITTED'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('TIN Certificate', response.data['detail'])

        # Optional-only upload does not unblock; mandatory upload does.
        self._upload(requirement=self.lease_req, filename='lease.pdf')
        response = self.client.post(
            f'/api/applications/{self.application.id}/transition/',
            {'to_status': 'SUBMITTED'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self._upload(requirement=self.tin_req)
        response = self.client.post(
            f'/api/applications/{self.application.id}/transition/',
            {'to_status': 'SUBMITTED'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.SUBMITTED)

    def test_upload_blocked_after_submission_for_applicants(self):
        self._upload(requirement=self.tin_req)
        self.client.force_authenticate(user=self.applicant)
        self.client.post(
            f'/api/applications/{self.application.id}/transition/',
            {'to_status': 'SUBMITTED'}, format='json',
        )
        response = self._upload(requirement=self.lease_req, filename='late.pdf')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_staff_can_upload_any_time(self):
        self._upload(requirement=self.tin_req)
        self.client.force_authenticate(user=self.applicant)
        self.client.post(
            f'/api/applications/{self.application.id}/transition/',
            {'to_status': 'SUBMITTED'}, format='json',
        )
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_authenticate(user=self.officer)
        response = self.client.post(
            f'/api/applications/{self.application.id}/upload_document/',
            {
                'file': SimpleUploadedFile('findings.jpg', b'fake', content_type='image/jpeg'),
                'requirement': self.lease_req.id,
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, 201, response.data)

    def test_status_history_exposed_for_timeline(self):
        """The application payload embeds the audit trail for the applicant timeline."""
        self.client.force_authenticate(user=self.applicant)
        self._upload(requirement=self.tin_req)
        self.client.post(
            f'/api/applications/{self.application.id}/transition/',
            {'to_status': 'SUBMITTED', 'note': 'All documents attached'}, format='json',
        )

        response = self.client.get('/api/applications/')
        row = next(r for r in response.data['results'] if r['id'] == self.application.id)
        self.assertEqual(len(row['history']), 1)
        entry = row['history'][0]
        self.assertEqual(entry['from_status'], 'DRAFT')
        self.assertEqual(entry['to_status'], 'SUBMITTED')
        self.assertIn('docapplicant', entry['changed_by_name'])
        self.assertEqual(entry['note'], 'All documents attached')
        self.assertIn('changed_at', entry)
