"""Tests for the business registration journey: BRELA -> TRA TIN -> LGA.

Now includes the NIDA + street identification letter gates.
"""
import base64
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from businesses.models import Business, BusinessDocument, TINApplication
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
    """TRA TIN applications: NIDA number + PDF copy of the ID are mandatory."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='jane', password='pass-12345678')
        self.client.force_authenticate(self.user)

    @staticmethod
    def _nida_copy():
        return SimpleUploadedFile('nida_copy.pdf', b'%PDF-1.4 NIDA copy', content_type='application/pdf')

    def test_apply_tin_returns_nine_digit_number(self):
        res = self.client.post('/api/businesses/demo/apply-tin/', {
            'business_name': 'Jane Traders', 'taxpayer_name': 'Jane Doe',
            'nida_number': '1' + '9' * 19, 'nida_copy': self._nida_copy(),
        }, format='multipart')
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.data['status'], 'APPROVED')
        self.assertEqual(len(res.data['tin_number']), 9)
        self.assertTrue(res.data['tin_number'].isdigit())
        self.assertEqual(res.data['nida_number'], '1' + '9' * 19)
        # The NIDA copy is stored with the application, like at TRA.
        self.assertEqual(len(res.data['documents']), 1)
        self.assertEqual(res.data['documents'][0]['kind'], 'NIDA_COPY')

    def test_apply_tin_requires_fields(self):
        res = self.client.post('/api/businesses/demo/apply-tin/', {'business_name': 'X'})
        self.assertEqual(res.status_code, 400)

    def test_apply_tin_requires_nida_number(self):
        res = self.client.post('/api/businesses/demo/apply-tin/', {
            'business_name': 'Jane Traders', 'taxpayer_name': 'Jane Doe',
            'nida_copy': self._nida_copy(),
        }, format='multipart')
        self.assertEqual(res.status_code, 400)
        self.assertIn('nida_number', str(res.content))

    def test_apply_tin_requires_nida_copy_pdf(self):
        res = self.client.post('/api/businesses/demo/apply-tin/', {
            'business_name': 'Jane Traders', 'taxpayer_name': 'Jane Doe',
            'nida_number': '1' + '9' * 19,
        }, format='multipart')
        self.assertEqual(res.status_code, 400)
        self.assertIn('nida_copy', str(res.content))

        # A non-PDF is rejected too.
        res2 = self.client.post('/api/businesses/demo/apply-tin/', {
            'business_name': 'Jane Traders', 'taxpayer_name': 'Jane Doe',
            'nida_number': '1' + '9' * 19,
            'nida_copy': SimpleUploadedFile('id.jpg', b'fake-image', content_type='image/jpeg'),
        }, format='multipart')
        self.assertEqual(res2.status_code, 400)
        self.assertIn('PDF', str(res2.content))

    def test_tin_applications_list_is_scoped_to_owner(self):
        other = User.objects.create_user(username='tom', password='pass-12345678')
        TINApplication.objects.create(applicant=other, business_name='Toms', taxpayer_name='Tom')
        self.client.post('/api/businesses/demo/apply-tin/', {
            'business_name': 'Jane Traders', 'taxpayer_name': 'Jane Doe',
            'nida_number': '1' + '9' * 19, 'nida_copy': self._nida_copy(),
        }, format='multipart')
        res = self.client.get('/api/businesses/tin-applications/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['business_name'], 'Jane Traders')


class NidaTests(TestCase):
    """NIDA capture, verification, and its gating behaviour."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='jane', password='pass-12345678')
        self.client.force_authenticate(self.user)

    def test_register_with_nida(self):
        res = self.client.post('/api/auth/register/', {
            'username': 'newgal', 'email': 'n@x.tz', 'first_name': 'New', 'last_name': 'Gal',
            'phone_number': '0712000111', 'password': 'Demo@12345',
            'nida_number': '1999' + '0' * 16,
        })
        self.assertEqual(res.status_code, 201, res.content)
        self.assertTrue(User.objects.get(username='newgal').nida_number)

    def test_register_rejects_short_nida(self):
        res = self.client.post('/api/auth/register/', {
            'username': 'newgal2', 'email': 'n2@x.tz', 'first_name': 'N', 'last_name': 'G',
            'phone_number': '0712000111', 'password': 'Demo@12345', 'nida_number': '12345',
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('20 digits', str(res.content))

    def test_verify_nida_endpoint(self):
        res = self.client.post('/api/auth/verify-nida/', {
            'nida_number': '1999' + '0' * 16, 'first_name': 'Jane', 'last_name': 'Doe',
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['valid'])
        res2 = self.client.post('/api/auth/verify-nida/', {'nida_number': '1234'})
        self.assertFalse(res2.data['valid'])

    def test_me_update_can_add_nida_later(self):
        res = self.client.patch('/api/auth/me/update/', {'nida_number': '2' + '0' * 19}, format='json')
        self.assertEqual(res.status_code, 200, res.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nida_number, '2' + '0' * 19)


class FullRegistrationJourneyTests(TestCase):
    """Register -> BRELA -> TRA TIN -> street letter -> business verified."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='jane', password='pass-12345678', nida_number='1' + '2' * 19,
        )
        self.client.force_authenticate(self.user)
        self.lga = LGA.objects.first() or self._make_lga()

    @staticmethod
    def _make_lga():
        return LGA.objects.create(region='Dar es Salaam', name='Ilala Municipal', code='IL')

    def _letter(self):
        return SimpleUploadedFile('street_letter.pdf', b'%PDF-1.4 street ID letter', content_type='application/pdf')

    def _journey(self, with_letter=True):
        brela = self.client.post('/api/businesses/demo/brela-register/', {'business_name': 'Jane Cafe'}).data
        tin = self.client.post('/api/businesses/demo/apply-tin/', {
            'business_name': 'Jane Cafe', 'taxpayer_name': 'Jane Doe',
            'nida_number': self.user.nida_number, 'nida_copy': self._letter(),
        }, format='multipart').data
        res = self.client.post('/api/businesses/', {
            'name': 'Jane Cafe',
            'tin_number': tin['tin_number'],
            'brela_registration_number': brela['registration_number'],
            'sector': 'Food',
            'location': {'lga': self.lga.id, 'ward': 'Ward A', 'street': 'Main St', 'plot_number': '1'},
        }, format='json')
        if with_letter and res.status_code == 201:
            # Wizard order: create -> upload street letter -> verify.
            self.client.post(
                f"/api/businesses/{res.data['id']}/street-id-letter/", {'file': self._letter()}, format='multipart'
            )
            self.client.post(f"/api/businesses/{res.data['id']}/verify/", {})
            res = self.client.get(f"/api/businesses/{res.data['id']}/")
        return brela, tin, res

    def test_create_requires_nida(self):
        User.objects.filter(pk=self.user.pk).update(nida_number='')
        self.user.refresh_from_db()
        res = self.client.post('/api/businesses/', {
            'name': 'No Nida Cafe', 'tin_number': '', 'brela_registration_number': '',
            'location': {'lga': self.lga.id, 'ward': 'W', 'street': 'S', 'plot_number': ''},
        }, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('NIDA', str(res.content))

    def test_create_requires_valid_numbers(self):
        res = self.client.post('/api/businesses/', {
            'name': 'Bad Numbers', 'tin_number': 'abc', 'brela_registration_number': 'x1',
            'location': {'lga': self.lga.id, 'ward': 'W', 'street': 'S', 'plot_number': ''},
        }, format='json')
        self.assertEqual(res.status_code, 400)

    def test_journey_creates_verified_business(self):
        brela, tin, res = self._journey()
        self.assertIn(res.status_code, (200, 201), res.content)
        self.assertTrue(res.data['is_verified'], res.content)
        business = Business.objects.get(owner=self.user, name='Jane Cafe')
        self.assertEqual(business.nida_number, self.user.nida_number)
        self.assertTrue(business.documents.filter(kind=BusinessDocument.Kinds.STREET_ID_LETTER).exists())

    def test_verify_blocked_without_street_letter(self):
        brela, tin, res = self._journey(with_letter=False)
        business_id = res.data['id']
        res2 = self.client.post(f'/api/businesses/{business_id}/verify/', {})
        self.assertEqual(res2.status_code, 400)
        self.assertIn('street identification letter', str(res2.content))

    def test_duplicate_business_name_rejected(self):
        self._journey()
        res = self.client.post('/api/businesses/', {
            'name': 'Jane Cafe', 'tin_number': '', 'brela_registration_number': '',
            'location': {'lga': self.lga.id, 'ward': 'Ward A', 'street': 'S', 'plot_number': ''},
        }, format='json')
        self.assertEqual(res.status_code, 400)
