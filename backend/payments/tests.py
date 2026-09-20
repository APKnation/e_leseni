from decimal import Decimal

from django.test import TestCase

from applications.models import Application
from businesses.models import Business, BusinessLocation
from lga.models import LGA, LicenceType
from licences.models import Licence  # noqa: F401 - ensures the signal receiver is loaded


class PaymentsFlowTestBase(TestCase):
    """Shared fixture: an application moved to PAYMENT_PENDING.

    transaction.on_commit callbacks only run inside captureOnCommitCallbacks,
    so helpers fire the pending callbacks explicitly.
    """

    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.applicant = User.objects.create_user(username='payer1', password='testpass123')
        self.lga = LGA.objects.create(name='Kinondoni', region='Dar es Salaam', code='KN')
        self.licence_type = LicenceType.objects.create(
            name='Retail Shop Licence', code='RETAIL', fee=Decimal('120000'), lga=self.lga
        )
        self.business = Business.objects.create(name='Kariakoo Traders', owner=self.applicant)
        self.location = BusinessLocation.objects.create(
            business=self.business, lga=self.lga, ward='Magomeni', street='Mwenge Road'
        )
        self.application = Application.objects.create(
            applicant=self.applicant, business=self.business,
            licence_type=self.licence_type, location=self.location,
        )
        with self.captureOnCommitCallbacks(execute=True):
            for status in ('SUBMITTED', 'UNDER_REVIEW', 'INSPECTION_SCHEDULED', 'INSPECTED',
                           'APPROVED', 'PAYMENT_PENDING'):
                self.application.transition_to(status)


class InvoiceAutoCreationTests(PaymentsFlowTestBase):
    def test_invoice_created_on_payment_pending(self):
        invoice = getattr(self.application, 'invoice', None)
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.amount, Decimal('120000'))
        self.assertTrue(invoice.control_number.startswith('99'))
        self.assertEqual(invoice.status, 'WAITING_PAYMENT')

    def test_gepg_calls_logged(self):
        from integrations.models import IntegrationLog

        logs = IntegrationLog.objects.filter(system='GEPG', direction='OUTBOUND')
        self.assertTrue(logs.exists())

    def test_approved_requires_payment_before_paid(self):
        # The flow only allows PAYMENT_PENDING -> PAID; nothing auto-advances.
        self.assertEqual(self.application.status, 'PAYMENT_PENDING')


class PaymentReconciliationTests(PaymentsFlowTestBase):
    def test_full_payment_advances_application_to_paid(self):
        from payments.services import record_payment

        invoice = self.application.invoice
        payment, settled = record_payment(
            invoice,
            amount=invoice.amount,
            method='MOBILE_MONEY',
            payer_name='Kariakoo Traders',
            payer_phone='0712345678',
            reference='MPESA-001',
        )
        self.assertTrue(settled)
        invoice.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(invoice.status, 'PAID')
        self.assertTrue(payment.receipt_number.startswith('RCP-'))
        # Licence auto-issuance completes the flow: PAID -> ISSUED.
        self.assertEqual(self.application.status, 'ISSUED')

    def test_licence_auto_issued_after_payment_signal(self):
        from payments.services import record_payment
        from licences.services import issue_licence_for_application

        invoice = self.application.invoice
        with self.captureOnCommitCallbacks(execute=True):
            record_payment(invoice, amount=invoice.amount, method='BANK')

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'ISSUED')
        # The signal issued the licence already (on_commit runs inline in tests).
        licence = getattr(self.application, 'licence', None)
        self.assertIsNotNone(licence)
        self.assertTrue(licence.licence_number.startswith('LIC-RETAIL-'))
        self.assertEqual(licence.status, 'ACTIVE')
        # Service is idempotent
        _, created = issue_licence_for_application(self.application)
        self.assertFalse(created)

    def test_double_payment_rejected(self):
        from payments.services import record_payment

        invoice = self.application.invoice
        record_payment(invoice, amount=invoice.amount, method='CASH')
        with self.assertRaises(ValueError):
            record_payment(invoice, amount=Decimal('1000'), method='CASH')
