from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from applications.models import Application
from businesses.models import Business, BusinessLocation
from lga.models import LGA, LicenceType
from licences.models import Licence  # noqa: F401 - loads the issuance receiver
from payments.models import Invoice  # noqa: F401


class SMSFlowTestBase(TestCase):
    """Fixture: applicant with a phone and an application ready to drive."""

    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.applicant = User.objects.create_user(
            username='smsuser', password='testpass123', phone_number='0712000111'
        )
        self.lga = LGA.objects.create(name='Moshi', region='Kilimanjaro', code='MO')
        self.licence_type = LicenceType.objects.create(
            name='Hardware Shop Licence', code='HW', fee=Decimal('80000'), lga=self.lga
        )
        self.business = Business.objects.create(name='Pwani Hardware', owner=self.applicant)
        self.location = BusinessLocation.objects.create(
            business=self.business, lga=self.lga, ward='Pasua', street='Old Moshi Road'
        )
        self.application = Application.objects.create(
            applicant=self.applicant, business=self.business,
            licence_type=self.licence_type, location=self.location,
        )

    def _to_payment_pending(self):
        with self.captureOnCommitCallbacks(execute=True):
            for status in ('SUBMITTED', 'UNDER_REVIEW', 'INSPECTION_SCHEDULED', 'INSPECTED',
                           'APPROVED', 'PAYMENT_PENDING'):
                self.application.transition_to(status)

    def _pay(self):
        from payments.services import record_payment

        invoice = self.application.invoice
        with self.captureOnCommitCallbacks(execute=True):
            payment, settled = record_payment(invoice, amount=invoice.amount, method='MOBILE_MONEY')
        self.assertTrue(settled)
        self.application.refresh_from_db()
        return payment


class SubmissionAndDecisionSMSTests(SMSFlowTestBase):
    def test_submission_sms_sent(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.application.transition_to('SUBMITTED')
        log = self.application.sms_logs.get(purpose='SUBMISSION')
        self.assertIn(self.application.reference_number, log.body)
        self.assertEqual(log.status, 'SENT')
        self.assertEqual(log.recipient, '0712000111')

    def test_approval_sms_sent(self):
        self._to_payment_pending()  # passes through APPROVED
        log = self.application.sms_logs.filter(purpose='APPROVAL').latest('id')
        self.assertIn('APPROVED', log.body)

    def test_rejection_sms_includes_reason(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.application.transition_to('SUBMITTED')
            self.application.transition_to('UNDER_REVIEW')
            self.application.transition_to('REJECTED', note='No TIN certificate')
        log = self.application.sms_logs.get(purpose='REJECTION')
        self.assertIn('No TIN certificate', log.body)

    def test_returned_for_correction_sms(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.application.transition_to('SUBMITTED')
            self.application.transition_to('UNDER_REVIEW')
            self.application.transition_to('RETURNED_FOR_CORRECTION')
        self.assertTrue(self.application.sms_logs.filter(purpose='CORRECTION').exists())


class ControlNumberAndPaymentSMSTests(SMSFlowTestBase):
    def test_control_number_sms_after_gepg(self):
        self._to_payment_pending()
        log = self.application.sms_logs.get(purpose='CONTROL_NUMBER')
        invoice = self.application.invoice
        self.assertIn(invoice.control_number, log.body)
        self.assertIn('80000', log.body)

    def test_payment_confirmed_sms(self):
        self._to_payment_pending()
        self._pay()
        log = self.application.sms_logs.get(purpose='PAYMENT_CONFIRMED')
        self.assertIn('80000', log.body)


class IssuanceSMSTests(SMSFlowTestBase):
    def test_issuance_sms_and_licence_link(self):
        self._to_payment_pending()
        self._pay()
        # Licence issuance transitions PAID -> ISSUED, which fires the SMS.
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'ISSUED')
        log = self.application.sms_logs.get(purpose='ISSUANCE')
        licence = self.application.licence
        self.assertIn(licence.licence_number, log.body)
        self.assertIn(licence.valid_until.isoformat(), log.body)


class NoPhoneSafetyTests(SMSFlowTestBase):
    def test_no_phone_does_not_break_flow(self):
        self.applicant.phone_number = ''
        self.applicant.save()
        with self.captureOnCommitCallbacks(execute=True):
            for status in ('SUBMITTED', 'UNDER_REVIEW', 'INSPECTION_SCHEDULED', 'INSPECTED',
                           'APPROVED', 'PAYMENT_PENDING'):
                self.application.transition_to(status)
        self.assertEqual(self.application.status, 'PAYMENT_PENDING')
        self.assertEqual(self.application.sms_logs.count(), 0)
        self.assertTrue(self.application.invoice.control_number)


class SMSLogAPITests(SMSFlowTestBase):
    def test_staff_can_list_logs(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        staff = User.objects.create_user(
            username='clerk', password='testpass123', role=User.Roles.OFFICER, is_staff=True
        )
        with self.captureOnCommitCallbacks(execute=True):
            self.application.transition_to('SUBMITTED')

        client = APIClient()
        client.force_authenticate(user=staff)
        response = client.get('/api/sms-logs/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['count'], 1)
