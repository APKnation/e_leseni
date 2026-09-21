"""USSD menu handler.

Implements the CON/END dialogue protocol used by Tanzanian USSD gateways
(Africa's Talking etc.). Each request supplies session_id, phone number and
the user's text so far; the handler returns the next screen prefixed with
CON (continue) or END (close the session).

Reuses the same domain services as the web app and API:
    - applications.models.Application.transition_to()
    - payments.services (control numbers + GePG reconciliation via record_payment)
    - accounts phone-based user lookup with auto-registration
"""
import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.crypto import get_random_string

from applications.models import Application
from payments.models import Invoice
from payments.services import record_payment

from .models import USSDSession

logger = logging.getLogger(__name__)

User = get_user_model()

MAIN_MENU = (
    'e-Leseni\n'
    '1. Apply for licence\n'
    '2. Check application status\n'
    '3. Get control number\n'
    '4. Pay invoice\n'
    '5. My licences\n'
    '0. Exit'
)

INVALID = '\nInvalid choice, try again.'
BACK = '\n0. Back'


def normalize_phone(raw):
    """Map gateway phone (255712345678 / 0712...) to the stored 07xx format."""
    digits = ''.join(ch for ch in (raw or '') if ch.isdigit())
    if digits.startswith('255'):
        return '0' + digits[3:]
    if len(digits) == 9:
        return '0' + digits
    return digits


def get_or_create_user(phone):
    """Find the account for this phone; auto-register applicants on first use."""
    normalized = normalize_phone(phone)
    user = User.objects.filter(phone_number__iexact=normalized).first()
    if user:
        return user, False
    username = f'ussd_{normalized or User.objects.count() + 1}'
    user = User.objects.create_user(
        username=username,
        password=get_random_string(12),
        phone_number=normalized or '0000000000',
        role=User.Roles.APPLICANT,
        first_name='USSD',
    )
    return user, True


def _numbered(items, label_fn):
    """Return (display_lines, {choice: item}) for a numbered list."""
    lines = []
    mapping = {}
    for index, item in enumerate(items, start=1):
        lines.append(f'{index}. {label_fn(item)}')
        mapping[str(index)] = item
    return '\n'.join(lines), mapping


class USSDHandler:
    """Routes one gateway request through the menu state machine."""

    def __init__(self, session_id, phone, text):
        self.session_id = session_id
        self.phone = phone
        self.input = text.split('*')[-1].strip() if text else ''
        self.session, created = USSDSession.objects.get_or_create(
            session_id=session_id,
            defaults={'phone_number': normalize_phone(phone)},
        )
        if created and self.input:
            # First request of a resumed gateway session already carries input.
            pass

    # -- entry point -------------------------------------------------------

    def handle(self):
        try:
            if not self.input:
                # No input = initial dial (or re-dial): show the main menu.
                # Identifying the user here also auto-registers first-time callers.
                self._user()
                self.session.state = USSDSession.State.START
                self.session.context = {}
                self.session.save(update_fields=['state', 'context', 'updated_at'])
                return f'CON {MAIN_MENU}'

            handler = {
                USSDSession.State.START: self._on_start,
                USSDSession.State.APPLY_LGA: self._on_apply_lga,
                USSDSession.State.APPLY_LICENCE: self._on_apply_licence,
                USSDSession.State.APPLY_BUSINESS: self._on_apply_business,
                USSDSession.State.STATUS_SELECT: self._on_status_select,
                USSDSession.State.PAY_SELECT_INVOICE: self._on_pay_select,
                USSDSession.State.PAY_PHONE: self._on_pay_phone,
            }.get(self.session.state, self._on_start)
            return handler()
        except Exception:
            logger.exception('USSD error session=%s', self.session_id)
            return self._end('Service temporarily unavailable. Please try again later.')

    # -- plumbing ------------------------------------------------------------

    def _continue(self, text, new_state=None, context_patch=None):
        if new_state:
            self.session.state = new_state
        if context_patch:
            self.session.context.update(context_patch)
        self.session.save(update_fields=['state', 'context', 'updated_at'])
        return f'CON {text}'

    def _end(self, text):
        self.session.state = USSDSession.State.EXITED
        self.session.save(update_fields=['state', 'updated_at'])
        return f'END {text}'

    def _user(self):
        user, created = get_or_create_user(self.phone)
        if created:
            logger.info('USSD auto-registered applicant for %s', self.session.phone_number)
        return user

    # -- main menu -------------------------------------------------------------

    def _on_start(self):
        choice = self.input
        if choice == '0':
            return self._end('Thank you for using e-Leseni.')
        if choice == '1':
            return self._continue(
                'Apply - choose council:\n' + self._lga_options() + BACK,
                USSDSession.State.APPLY_LGA,
            )
        if choice == '2':
            apps = list(
                Application.objects.filter(applicant=self._user())
                .exclude(status=Application.Status.DRAFT)
                .order_by('-created_at')[:5]
            )
            if not apps:
                return self._end('You have no applications yet. Dial again and choose 1 to apply.')
            lines, mapping = _numbered(
                apps, lambda a: f'{a.reference_number} ({a.get_status_display()})'
            )
            return self._continue(
                f'Status - pick application:\n{lines}{BACK}',
                USSDSession.State.STATUS_SELECT,
                {'status_ids': {k: v.pk for k, v in mapping.items()}},
            )
        if choice in {'3', '4'}:
            label = 'Get control number' if choice == '3' else 'Pay invoice'
            return self._show_pending_invoices(label)
        if choice == '5':
            return self._show_licences()
        return self._continue(MAIN_MENU + INVALID, USSDSession.State.START)

    # -- apply -------------------------------------------------------------------

    def _lga_options(self, max_options=8):
        from lga.models import LGA

        lgas = list(LGA.objects.order_by('name')[:max_options])
        lines, mapping = _numbered(lgas, lambda l: f'{l.name} ({l.region})')
        self.session.context['lga_ids'] = {k: v.pk for k, v in mapping.items()}
        self.session.save(update_fields=['context', 'updated_at'])
        return '\n'.join(lines)

    def _on_apply_lga(self):
        from lga.models import LicenceType

        lga_ids = self.session.context.get('lga_ids', {})
        if self.input == '0':
            return self._continue(MAIN_MENU, USSDSession.State.START)
        if self.input not in lga_ids:
            return self._continue(
                'Apply - choose council:\n' + self._lga_options() + INVALID + BACK,
                USSDSession.State.APPLY_LGA,
            )
        licence_types = list(
            LicenceType.objects.filter(
                lga_id=lga_ids[self.input], category=LicenceType.Category.BUSINESS
            )
        )
        if not licence_types:
            return self._end('No licences available in this council yet.')
        lines, mapping = _numbered(licence_types, lambda t: f'{t.name} - {t.fee} TZS')
        return self._continue(
            f'Choose licence:\n{lines}{BACK}',
            USSDSession.State.APPLY_LICENCE,
            {'licence_ids': {k: v.pk for k, v in mapping.items()}},
        )

    def _on_apply_licence(self):
        licence_ids = self.session.context.get('licence_ids', {})
        if self.input == '0':
            return self._continue(
                'Apply - choose council:\n' + self._lga_options() + BACK,
                USSDSession.State.APPLY_LGA,
            )
        if self.input not in licence_ids:
            return self._continue('Invalid choice.' + BACK, USSDSession.State.APPLY_LICENCE)
        self.session.context['licence_id'] = licence_ids[self.input]
        self.session.save(update_fields=['context', 'updated_at'])

        businesses = list(self._user().businesses.all())
        if not businesses:
            return self._continue(
                'Enter your business name to register:',
                USSDSession.State.APPLY_BUSINESS,
                {'new_business': True},
            )
        lines, mapping = _numbered(businesses, lambda b: b.name)
        extra = f'{len(businesses) + 1}. Register a new business'
        return self._continue(
            f'Choose business:\n{lines}\n{extra}{BACK}',
            USSDSession.State.APPLY_BUSINESS,
            {'business_ids': {k: v.pk for k, v in mapping.items()}},
        )

    def _on_apply_business(self):
        ctx = self.session.context
        if self.input == '0':
            return self._continue(MAIN_MENU, USSDSession.State.START)
        if ctx.get('new_business'):
            name = self.input[:200]
            if len(name) < 3:
                return self._continue(
                    'Name too short. Enter your business name:',
                    USSDSession.State.APPLY_BUSINESS,
                )
            return self._submit_application(new_business_name=name)
        business_ids = ctx.get('business_ids', {})
        next_new = str(len(business_ids) + 1)
        if self.input == next_new:
            return self._continue(
                'Enter your business name to register:',
                USSDSession.State.APPLY_BUSINESS,
                {'new_business': True},
            )
        if self.input in business_ids:
            return self._submit_application(business_id=business_ids[self.input])
        return self._continue('Invalid choice.' + BACK, USSDSession.State.APPLY_BUSINESS)

    @transaction.atomic
    def _submit_application(self, business_id=None, new_business_name=None):
        from businesses.models import Business, BusinessLocation
        from lga.models import LicenceType

        user = self._user()
        licence_id = self.session.context.get('licence_id')
        if not licence_id:
            return self._end('Session expired. Please dial again.')
        licence_type = LicenceType.objects.select_related('lga').get(pk=licence_id)

        if new_business_name:
            business = Business.objects.create(
                owner=user, name=new_business_name, sector='USSD registration'
            )
            BusinessLocation.objects.create(
                business=business, lga=licence_type.lga,
                ward='USSD', street='USSD', is_primary=True,
            )
        else:
            business = Business.objects.get(pk=business_id, owner=user)

        location = (
            BusinessLocation.objects.filter(business=business).first()
            or BusinessLocation.objects.create(
                business=business, lga=licence_type.lga,
                ward='USSD', street='USSD', is_primary=True,
            )
        )

        application = Application.objects.create(
            applicant=user, business=business,
            licence_type=licence_type, location=location,
            purpose_statement='Submitted via USSD',
        )
        application.transition_to(Application.Status.SUBMITTED, by=user)
        return self._end(
            f'Application {application.reference_number} submitted! '
            'You will receive SMS updates.'
        )

    # -- status ---------------------------------------------------------------------

    def _on_status_select(self):
        status_ids = self.session.context.get('status_ids', {})
        if self.input == '0':
            return self._continue(MAIN_MENU, USSDSession.State.START)
        if self.input not in status_ids:
            return self._continue('Invalid choice.' + BACK, USSDSession.State.STATUS_SELECT)
        application = Application.objects.get(pk=status_ids[self.input])
        last_change = application.history.order_by('-changed_at').first()
        last_line = (
            f'Last update: {last_change.changed_at:%d %b %Y}'
            if last_change else 'No updates yet'
        )
        return self._end(
            f'{application.reference_number}\n'
            f'{application.licence_type.name}\n'
            f'Status: {application.get_status_display()}\n'
            f'{last_line}'
        )

    # -- payments ----------------------------------------------------------------------

    def _show_pending_invoices(self, label):
        user = self._user()
        invoices = list(
            Invoice.objects.filter(
                application__applicant=user,
                status__in=[Invoice.Status.WAITING_PAYMENT, Invoice.Status.PENDING],
            )
            .select_related('application')
            .order_by('-issued_at')[:5]
        )
        if not invoices:
            return self._end(f'{label}: you have no pending invoices.')
        lines, mapping = _numbered(
            invoices,
            lambda inv: f'{inv.application.reference_number} {inv.amount} {inv.currency}',
        )
        return self._continue(
            f'{label} - pick invoice:\n{lines}{BACK}',
            USSDSession.State.PAY_SELECT_INVOICE,
            {'invoice_ids': {k: v.pk for k, v in mapping.items()}},
        )

    def _on_pay_select(self):
        invoice_ids = self.session.context.get('invoice_ids', {})
        if self.input == '0':
            return self._continue(MAIN_MENU, USSDSession.State.START)
        if self.input not in invoice_ids:
            return self._continue('Invalid choice.' + BACK, USSDSession.State.PAY_SELECT_INVOICE)
        invoice = Invoice.objects.select_related('application').get(pk=invoice_ids[self.input])
        self.session.context['paying_invoice_id'] = invoice.pk
        self.session.save(update_fields=['context', 'updated_at'])
        return self._continue(
            f'Pay {invoice.amount} {invoice.currency} for '
            f'{invoice.application.reference_number}.\n'
            'Enter your mobile money PIN to confirm:',
            USSDSession.State.PAY_PHONE,
        )

    def _on_pay_phone(self):
        """Final confirmation step: user enters 1 to confirm (or anything else cancels)."""
        phone = normalize_phone(self.session.phone_number)
        invoice_id = self.session.context.get('paying_invoice_id')
        if self.input != '1':
            return self._end('Payment cancelled. Dial again to restart.')
        invoice = Invoice.objects.select_related('application').get(pk=invoice_id)
        try:
            payment, settled = record_payment(
                invoice,
                amount=invoice.amount,
                method='MOBILE_MONEY',
                payer_name=invoice.application.business.owner.get_full_name(),
                payer_phone=phone,
                reference=f'USSD-{self.session_id[:12]}',
            )
        except ValueError as exc:
            return self._end(f'Payment failed: {exc}')
        receipt = payment.receipt_number or 'pending'
        if settled:
            return self._end(
                f'Payment of {invoice.amount} {invoice.currency} received! '
                f'Receipt {receipt}. Licence processing follows.'
            )
        return self._end('Payment recorded. Reconciliation pending - SMS will follow.')
