"""Council catalogue permissions: officers manage only their own LGA."""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from lga.models import LGA, LicenceType


class CouncilCataloguePermissionTests(TestCase):
    """Licence types: public read, OFFICER/ADMIN write, LGA-scoped for officers."""

    def setUp(self):
        self.client = APIClient()
        self.ilala = LGA.objects.create(region='Dar es Salaam', name='Ilala', code='DS-ILALA')
        self.mufindi = LGA.objects.create(region='Iringa', name='Mufindi', code='MU-MUFINDI')
        self.officer = User.objects.create_user(
            username='cat_officer', password='pass-12345678', role='OFFICER', lga=self.ilala,
        )
        self.inspector = User.objects.create_user(
            username='cat_inspector', password='pass-12345678', role='INSPECTOR', lga=self.ilala,
        )
        self.ilala_lt = LicenceType.objects.create(
            name='Ilala Food Licence', code='IL-FOOD', fee=50000, lga=self.ilala,
        )
        self.mufindi_lt = LicenceType.objects.create(
            name='Mufindi Food Licence', code='MU-FOOD', fee=40000, lga=self.mufindi,
        )

    def test_public_read_stays_open(self):
        res = self.client.get('/api/licence-types/')
        self.assertEqual(res.status_code, 200)

    def test_officer_updates_own_council_licence(self):
        self.client.force_authenticate(self.officer)
        res = self.client.patch(
            f'/api/licence-types/{self.ilala_lt.id}/', {'fee': '55000'}, format='json'
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.ilala_lt.refresh_from_db()
        self.assertEqual(self.ilala_lt.fee, 55000)

    def test_officer_cannot_touch_another_council(self):
        self.client.force_authenticate(self.officer)
        res = self.client.patch(
            f'/api/licence-types/{self.mufindi_lt.id}/', {'fee': '1'}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_inspector_cannot_write_catalogue(self):
        self.client.force_authenticate(self.inspector)
        res = self.client.patch(
            f'/api/licence-types/{self.ilala_lt.id}/', {'fee': '1'}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_officer_new_licence_type_is_pinned_to_own_lga(self):
        """A payload pointing at another council is overridden server-side."""
        self.client.force_authenticate(self.officer)
        res = self.client.post('/api/licence-types/', {
            'name': 'Boda Stand', 'code': 'IL-BODA', 'fee': '30000',
            'validity_months': 12, 'lga': self.mufindi.id,
        }, format='json')
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.data['lga'], self.ilala.id)
