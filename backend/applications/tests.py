from django.test import TestCase

from businesses.models import Business, BusinessLocation
from lga.models import LGA, LicenceType

from .models import Application


class ApplicationStatusFlowTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.applicant = User.objects.create_user(username='applicant1', password='testpass123')
        self.lga = LGA.objects.create(name='Ilala', region='Dar es Salaam', code='IL')
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
        self.assertTrue(self.application.reference_number.endswith('00001'))

    def test_happy_path_to_issued(self):
        app = self.application
        path = [
            'SUBMITTED',
            'UNDER_REVIEW',
            'INSPECTION_SCHEDULED',
            'INSPECTED',
            'APPROVED',
            'PAYMENT_PENDING',
            'PAID',
            'ISSUED',
        ]
        for i, status in enumerate(path):
            app.transition_to(status, by=self.applicant)
            self.assertEqual(app.status, status)
        self.assertEqual(app.history.count(), len(path))

    def test_invalid_transition_rejected(self):
        with self.assertRaises(ValueError):
            self.application.transition_to('APPROVED')

    def test_returned_for_correction_loop(self):
        app = self.application
        app.transition_to('SUBMITTED')
        app.transition_to('UNDER_REVIEW')
        app.transition_to('RETURNED_FOR_CORRECTION')
        self.assertEqual(app.status, 'RETURNED_FOR_CORRECTION')
        app.transition_to('DRAFT')
        self.assertEqual(app.status, 'DRAFT')
        # And it can be resubmitted
        app.transition_to('SUBMITTED')
        self.assertEqual(app.status, 'SUBMITTED')

    def test_rejection_branch(self):
        app = self.application
        app.transition_to('SUBMITTED')
        app.transition_to('UNDER_REVIEW')
        app.transition_to('REJECTED', note='Missing TIN certificate')
        self.assertEqual(app.status, 'REJECTED')
        self.assertEqual(app.rejection_reason, 'Missing TIN certificate')
        self.assertIsNotNone(app.decided_at)
        # Terminal state
        with self.assertRaises(ValueError):
            app.transition_to('DRAFT')

    def test_issued_is_terminal(self):
        app = self.application
        for status in ['SUBMITTED', 'UNDER_REVIEW', 'INSPECTION_SCHEDULED', 'INSPECTED',
                       'APPROVED', 'PAYMENT_PENDING', 'PAID', 'ISSUED']:
            app.transition_to(status)
        with self.assertRaises(ValueError):
            app.transition_to('DRAFT')
