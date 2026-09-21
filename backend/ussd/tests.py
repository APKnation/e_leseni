from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from applications.models import Application
from businesses.models import Business, BusinessLocation
from lga.models import LGA, LicenceType
from payments.models import Invoice
from ussd.models import USSDSession


def ussd(text, session_id='ATUid_12345', phone='255712000111'):
    """Post a simulated gateway request and return the response text."""
    from django.test import Client

    response = Client().post(
        reverse('ussd-gateway'),
        {'sessionId': session_id, 'phoneNumber': phone, 'text': text},
    )
    return response.content.decode()


class USSDFlowTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.user = User.objects.create_user(
            username='ussd_user', password='testpass123', phone_number='0712000111'
        )
        self.lga = LGA.objects.create(name='Ilala', region='Dar es Salaam', code='DS-ILALA')
        self.licence = LicenceType.objects.create(
            name='Business Licence', code='DS-ILALA-BUS', fee=50000, lga=self.lga
        )
        self.business = Business.objects.create(owner=self.user, name='Mama Ntilie')
        BusinessLocation.objects.create(
            business=self.business, lga=self.lga, ward='Upanga', street='Ocean Road', is_primary=True
        )

    def test_main_menu_renders(self):
        output = ussd('')
        self.assertTrue(output.startswith('CON'))
        self.assertIn('Apply for licence', output)

    def test_exit(self):
        output = ussd('0', session_id='s-exit')
        self.assertTrue(output.startswith('END'))

    def test_invalid_menu_choice(self):
        output = ussd('9', session_id='s-inv')
        self.assertTrue(output.startswith('CON'))
        self.assertIn('Invalid', output)

    def test_status_check_with_no_applications(self):
        output = ussd('2', session_id='s-status-empty')
        self.assertTrue(output.startswith('END'))
        self.assertIn('no applications', output)

    def test_status_check_shows_application(self):
        app = Application.objects.create(
            applicant=self.user, business=self.business,
            licence_type=self.licence,
            location=BusinessLocation.objects.filter(business=self.business).first(),
        )
        app.transition_to(Application.Status.SUBMITTED)

        output = ussd('2', session_id='s-status')      # main menu -> status
        self.assertTrue(output.startswith('CON'))
        output = ussd('2*1', session_id='s-status')    # pick first application
        self.assertTrue(output.startswith('END'))
        self.assertIn(app.reference_number, output)
        self.assertIn('Submitted', output)

    def test_full_apply_flow_with_existing_business(self):
        session_id = 's-apply'
        out1 = ussd('1', session_id)                    # apply
        self.assertIn('choose council', out1)
        out2 = ussd('1*1', session_id)                  # first council
        self.assertIn('Choose licence', out2)
        out3 = ussd('1*1*1', session_id)                # first licence
        self.assertIn('Choose business', out3)
        out4 = ussd('1*1*1*1', session_id)              # first business
        self.assertTrue(out4.startswith('END'), out4)
        self.assertIn('submitted', out4)

        app = Application.objects.get(applicant=self.user, business=self.business)
        self.assertEqual(app.status, Application.Status.SUBMITTED)
        self.assertIn('USSD', app.purpose_statement)

    def test_apply_auto_registers_new_business(self):
        session_id = 's-newbiz'
        ussd('1', session_id)
        ussd('1*1', session_id)
        ussd('1*1*1', session_id)
        # Choose "register new business" (businesses exist -> choice 2), then type name
        out = ussd('1*1*1*2', session_id)
        self.assertIn('Enter your business name', out)
        out = ussd('1*1*1*2*Neema Salon', session_id)
        self.assertTrue(out.startswith('END'))
        self.assertTrue(Business.objects.filter(owner=self.user, name='Neema Salon').exists())
        app = Application.objects.get(business__name='Neema Salon')
        self.assertEqual(app.status, Application.Status.SUBMITTED)

    def test_apply_with_no_business_registers_one(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        fresh = User.objects.create_user(
            username='fresh', password='testpass123', phone_number='0712000222'
        )
        self.assertFalse(Business.objects.filter(owner=fresh).exists())

        session_id = 's-fresh'
        phone = '255712000222'
        ussd('1', session_id, phone=phone)
        ussd('1*1', session_id, phone=phone)
        ussd('1*1*1', session_id, phone=phone)
        out = ussd('1*1*1*Zawadi Shop', session_id, phone=phone)
        self.assertTrue(out.startswith('END'), out)
        self.assertTrue(Business.objects.filter(owner=fresh, name='Zawadi Shop').exists())

    def test_unknown_phone_auto_registers_applicant(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        ussd('', session_id='s-autoreg', phone='255713999888')
        user = User.objects.filter(phone_number='0713999888').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, User.Roles.APPLICANT)
        self.assertTrue(user.username.startswith('ussd_'))


class USSDPaymentTests(TestCase):
    """Payment dialogues; default gateway phone maps to ussd_pay (0712000333)."""
    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.user = User.objects.create_user(
            username='ussd_pay', password='testpass123', phone_number='0712000333'
        )
        self.lga = LGA.objects.create(name='Ilala', region='Dar es Salaam', code='DS-ILALA-2')
        self.licence = LicenceType.objects.create(
            name='Business Licence', code='DS-ILALA-2-BUS', fee=50000, lga=self.lga
        )
        self.business = Business.objects.create(owner=self.user, name='Pay Shop')
        self.location = BusinessLocation.objects.create(
            business=self.business, lga=self.lga, ward='Upanga', street='Ocean Road', is_primary=True
        )
        self.application = Application.objects.create(
            applicant=self.user, business=self.business,
            licence_type=self.licence, location=self.location,
        )
        for status_ in ('SUBMITTED', 'UNDER_REVIEW', 'INSPECTION_SCHEDULED', 'INSPECTED',
                        'APPROVED', 'PAYMENT_PENDING'):
            with self.captureOnCommitCallbacks(execute=True):
                self.application.transition_to(status_)
        # Invoice is auto-created by the payments signal (on_commit callbacks above).
        self.assertTrue(hasattr(self.application, 'invoice'))

    def test_get_control_number_flow(self):
        output = ussd('3', session_id='s-cn', phone='255712000333')
        self.assertTrue(output.startswith('CON'))
        self.assertIn(self.application.reference_number, output)
        output = ussd('3*1', session_id='s-cn', phone='255712000333')
        # The confirmation screen repeats the amount before the final step
        self.assertTrue(output.startswith('CON'), output)

    def test_pay_flow_advances_application(self):
        session_id = 's-pay'
        phone = '255712000333'
        out = ussd('4', session_id, phone=phone)
        self.assertIn(self.application.reference_number, out)
        out = ussd('4*1', session_id, phone=phone)      # pick invoice
        self.assertIn('Pay 50000', out)
        out = ussd('4*1*1', session_id, phone=phone)    # confirm with 1
        self.assertTrue(out.startswith('END'), out)
        self.assertIn('received', out)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.PAID)
        invoice = Invoice.objects.get(application=self.application)
        self.assertEqual(invoice.status, 'PAID')

    def test_pay_cancelled(self):
        session_id = 's-cancel'
        phone = '255712000333'
        ussd('4', session_id, phone=phone)
        ussd('4*1', session_id, phone=phone)
        out = ussd('4*1*5', session_id, phone=phone)   # anything but 1 cancels
        self.assertIn('cancelled', out.lower())
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.PAYMENT_PENDING)
