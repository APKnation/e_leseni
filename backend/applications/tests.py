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
        self.applicant = User.objects.create_user(username='applicant1', password='testpass123')
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
            username='multi1', password='testpass123', phone_number='0755000111'
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
        other = User.objects.create_user(username='other2', password='testpass123')

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
        self.user = User.objects.create_user(username='dup1', password='testpass123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_duplicate_name_for_same_owner_blocked(self):
        Business.objects.create(owner=self.user, name='Same Name Ltd')
        response = self.client.post('/api/businesses/', {'name': 'Same Name Ltd'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_name_different_owners_ok(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other = User.objects.create_user(username='dup2', password='testpass123')
        Business.objects.create(owner=other, name='Kariakoo Traders')

        response = self.client.post('/api/businesses/', {'name': 'Kariakoo Traders'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
