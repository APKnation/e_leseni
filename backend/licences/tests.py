from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from applications.models import Application
from businesses.models import Business, BusinessLocation
from lga.models import LGA, LicenceType
from licences.models import Licence, Renewal


class LicenceIssueTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.applicant = User.objects.create_user(username='holder1', password='testpass123')
        self.lga = LGA.objects.create(name='Temeke', region='Dar es Salaam', code='TK')
        self.licence_type = LicenceType.objects.create(
            name='Food Vendor Licence', code='FOOD', fee=50000, validity_months=12, lga=self.lga
        )
        self.business = Business.objects.create(name='Chang\'ombe Foods', owner=self.applicant)
        self.location = BusinessLocation.objects.create(
            business=self.business, lga=self.lga, ward='Chang\'ombe', street='Nyerere Road'
        )
        self.application = Application.objects.create(
            applicant=self.applicant, business=self.business,
            licence_type=self.licence_type, location=self.location,
        )
        self.application.status = Application.Status.PAID
        self.application.save()

    def test_issue_and_qr_payload(self):
        from licences.services import build_qr_payload, issue_licence_for_application

        licence, created = issue_licence_for_application(self.application)
        self.assertTrue(created)
        self.assertTrue(licence.licence_number.startswith('LIC-FOOD-'))
        self.assertEqual(licence.valid_until - licence.valid_from, timedelta(days=365))
        payload = build_qr_payload(licence)
        self.assertIn(licence.qr_token, payload)

    def test_verify_endpoint_valid(self):
        from licences.services import issue_licence_for_application

        licence, _ = issue_licence_for_application(self.application)
        client = APIClient()
        response = client.get(f'/api/licences/verify/{licence.qr_token}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['valid'])
        self.assertEqual(response.data['licence_number'], licence.licence_number)

    def test_verify_endpoint_unknown_token(self):
        client = APIClient()
        response = client.get('/api/licences/verify/no-such-token/')
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data['valid'])

    def test_verify_shows_expired(self):
        from licences.services import issue_licence_for_application

        licence, _ = issue_licence_for_application(self.application)
        Licence.objects.filter(pk=licence.pk).update(valid_until=date.today() - timedelta(days=1))
        licence.refresh_from_db()
        client = APIClient()
        response = client.get(f'/api/licences/verify/{licence.qr_token}/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['valid'])
        self.assertTrue(response.data['is_expired'])


class RenewalTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.applicant = User.objects.create_user(username='holder2', password='testpass123')
        self.admin = User.objects.create_user(
            username='admin1', password='testpass123',
            is_staff=True, role=User.Roles.ADMIN,
        )
        self.lga = LGA.objects.create(name='Ilala', region='Dar es Salaam', code='IL')
        self.licence_type = LicenceType.objects.create(
            name='Kiosk Licence', code='KIOSK', fee=30000, validity_months=12, lga=self.lga
        )
        self.business = Business.objects.create(name='Kiosk Yako', owner=self.applicant)
        self.location = BusinessLocation.objects.create(
            business=self.business, lga=self.lga, ward='Ilala', street='Sokoine Drive'
        )
        self.application = Application.objects.create(
            applicant=self.applicant, business=self.business,
            licence_type=self.licence_type, location=self.location,
        )
        self.application.status = Application.Status.PAID
        self.application.save()
        from licences.services import issue_licence_for_application

        self.licence, _ = issue_licence_for_application(self.application)

    def test_renew_request_and_approve(self):
        client = APIClient()
        client.force_authenticate(user=self.applicant)

        response = client.post(f'/api/licences/{self.licence.pk}/renew/')
        self.assertEqual(response.status_code, 201)
        self.licence.refresh_from_db()
        self.assertEqual(self.licence.status, Licence.Status.RENEWAL_PENDING)

        # Double renewal blocked
        response2 = client.post(f'/api/licences/{self.licence.pk}/renew/')
        self.assertEqual(response2.status_code, 409)

        # Staff approves
        admin_client = APIClient()
        admin_client.force_authenticate(user=self.admin)
        renewal = Renewal.objects.get(licence=self.licence)
        response3 = admin_client.post(f'/api/renewals/{renewal.pk}/decide/', {'decision': 'approve'})
        self.assertEqual(response3.status_code, 200)
        renewal.refresh_from_db()
        self.assertEqual(renewal.status, Renewal.Status.APPROVED)
        self.assertEqual(renewal.new_valid_until, self.licence.valid_until.replace(
            year=self.licence.valid_until.year + 1
        ))

    def test_renewal_list_scoped_to_owner(self):
        from django.contrib.auth import get_user_model

        other = get_user_model().objects.create_user(username='other1', password='testpass123')
        client = APIClient()
        client.force_authenticate(user=other)
        response = client.get('/api/renewals/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
