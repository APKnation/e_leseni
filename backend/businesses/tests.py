"""Tests for the business registration journey: BRELA -> TRA TIN -> LGA."""

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from businesses.models import Business, TINApplication
from lga.models import LGA


class BrelaRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='jane', password='pass-12345678')
        self.client.force_authenticate(self.user)

    def test_brela_register_returns_usable_registration_number(self):
        res = self.client.post('/api/businesses/demo/brela-register/', {'business_name': 'Jane Traders'})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['registered'])
        self.assertTrue(str(res.data['registration_number']).startswith('1'))

    def test_brela_register_requires_name(self):
        res = self.client.post('/api/businesses/demo/brela-register/', {})
        self.assertEqual(res.status_code, 400)


class TINApplicationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='jane', password='pass-12345678')
        self.client.force_authenticate(self.user)

    def test_apply_tin_returns_nine_digit_number(self):
        res = self.client.post('/api/businesses/demo/apply-tin/', {
            'business_name': 'Jane Traders', 'taxpayer_name': 'Jane Doe',
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['status'], 'APPROVED')
        self.assertEqual(len(res.data['tin_number']), 9)
        self.assertTrue(res.data['tin_number'].isdigit())

    def test_apply_tin_requires_fields(self):
        res = self.client.post('/api/businesses/demo/apply-tin/', {'business_name': 'X'})
        self.assertEqual(res.status_code, 400)

    def test_tin_applications_list_is_scoped_to_owner(self):
        other = User.objects.create_user(username='tom', password='pass-12345678')
        TINApplication.objects.create(applicant=other, business_name='Toms', taxpayer_name='Tom')
        self.client.post('/api/businesses/demo/apply-tin/', {
            'business_name': 'Jane Traders', 'taxpayer_name': 'Jane Doe',
        })
        res = self.client.get('/api/businesses/tin-applications/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['business_name'], 'Jane Traders')


class FullRegistrationJourneyTests(TestCase):
    """Register -> BRELA -> TRA TIN -> business verified, like the frontend wizard."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='jane', password='pass-12345678')
        self.client.force_authenticate(self.user)
        self.lga = LGA.objects.first() or self._make_lga()

    @staticmethod
    def _make_lga():
        return LGA.objects.create(region='Dar es Salaam', name='Ilala Municipal', code='IL')

    def _journey(self):
        brela = self.client.post('/api/businesses/demo/brela-register/', {'business_name': 'Jane Cafe'}).data
        tin = self.client.post('/api/businesses/demo/apply-tin/', {
            'business_name': 'Jane Cafe', 'taxpayer_name': 'Jane Doe',
        }).data
        res = self.client.post('/api/businesses/', {
            'name': 'Jane Cafe',
            'tin_number': tin['tin_number'],
            'brela_registration_number': brela['registration_number'],
            'sector': 'Food',
            'location': {'lga': self.lga.id, 'ward': 'Ward A', 'street': 'Main St', 'plot_number': '1'},
        }, format='json')
        return brela, tin, res

    def test_journey_creates_verified_business(self):
        brela, tin, res = self._journey()
        self.assertEqual(res.status_code, 201, res.content)
        self.assertTrue(res.data['is_verified'])
        self.assertTrue(Business.objects.filter(owner=self.user, name='Jane Cafe').exists())

    def test_unverified_business_can_verify_later(self):
        brela, tin, res = self._journey()
        business_id = res.data['id']
        Business.objects.filter(pk=business_id).update(is_verified=False)
        res2 = self.client.post(f'/api/businesses/{business_id}/verify/', {})
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.data['is_verified'])

    def test_duplicate_business_name_rejected(self):
        self._journey()
        res = self.client.post('/api/businesses/', {
            'name': 'Jane Cafe', 'tin_number': '', 'brela_registration_number': '',
            'location': {'lga': self.lga.id, 'ward': 'Ward A', 'street': 'S', 'plot_number': ''},
        }, format='json')
        self.assertEqual(res.status_code, 400)
