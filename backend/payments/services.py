"""Payment services: invoice creation, GePG control numbers, reconciliation.

These functions are called from the status-change signal receiver and from
the API layer. All external calls go through the integrations adapters.
"""
import logging

from django.db import transaction
from django.utils import timezone

from applications.models import Application
from integrations.adapters import GePGAdapter

from .models import Invoice, Payment

logger = logging.getLogger(__name__)


def create_invoice_for_application(application):
    """Create (or return the existing) invoice for an application.

    Amount is taken from the licence type fee. Idempotent: safe to call
    multiple times for the same application.
    """
    if getattr(application, 'invoice', None):
        return application.invoice, False

    invoice = Invoice.objects.create(
        application=application,
        amount=application.licence_type.fee,
        currency='TZS',
    )
    logger.info('Invoice %s created for %s', invoice.pk, application.reference_number)
    return invoice, True


def request_control_number(invoice):
    """Ask GePG for a control number and mark the invoice WAITING_PAYMENT."""
    if invoice.status not in {Invoice.Status.PENDING, Invoice.Status.EXPIRED}:
        return invoice, False

    result = GePGAdapter().request_control_number(
        bill_amount=invoice.amount,
        bill_reference=invoice.application.reference_number,
        payer_name=invoice.application.business.owner.get_full_name() or invoice.application.business.owner.username,
        description=f'{invoice.application.licence_type.name} licence fee',
    )
    if not result.success:
        logger.error('GePG bill request failed for invoice %s: %s', invoice.pk, result.error)
        return invoice, False

    invoice.control_number = result.data['control_number']
    invoice.gepg_bill_id = result.data.get('bill_id', '')
    invoice.status = Invoice.Status.WAITING_PAYMENT
    invoice.control_number_expires_at = timezone.now() + timezone.timedelta(days=30)
    invoice.save(update_fields=['control_number', 'gepg_bill_id', 'status', 'control_number_expires_at', 'updated_at'])

    _notify_control_number(application=invoice.application, invoice=invoice)
    return invoice, True


def _notify_control_number(*, application, invoice):
    """Best-effort SMS with the control number once GePG issues one."""
    try:
        from notifications import services as notifications_services

        phone = (application.applicant.phone_number or '').strip()
        if phone:
            notifications_services.control_number_issued(
                application, phone,
                control_number=invoice.control_number,
                amount=invoice.amount,
                currency=invoice.currency,
            )
    except Exception:  # noqa: BLE001 - SMS must never break payments
        logger.exception('Control-number SMS failed for %s', application.reference_number)


def record_payment(invoice, *, amount, method, payer_name='', payer_phone='', reference=''):
    """Record a payment, reconcile with GePG, and advance the application.

    Marks the invoice PAID only when GePG confirms (mock) AND the invoice is
    fully covered. When the invoice settles, the application is moved from
    PAYMENT_PENDING to PAID - which in turn triggers licence issuance.
    """
    if invoice.status == Invoice.Status.CANCELLED:
        raise ValueError('Cannot pay a cancelled invoice.')
    if invoice.status == Invoice.Status.PAID:
        raise ValueError('Invoice is already settled.')

    with transaction.atomic():
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            method=method,
            payer_name=payer_name,
            payer_phone=payer_phone,
            reference=reference,
        )

        # Reconcile with GePG (mock in dev). A real deployment would handle
        # async callbacks; here we reconcile synchronously.
        reconcile = GePGAdapter().reconcile_payment(
            control_number=invoice.control_number,
            amount_paid=payment.amount,
        )
        if not reconcile.success:
            # Keep the payment record but leave the invoice unsettled for retry.
            logger.error('GePG reconciliation failed for invoice %s: %s', invoice.pk, reconcile.error)
            return payment, False

        receipt = reconcile.data.get('receipt_number', '')
        if receipt:
            payment.receipt_number = receipt
            payment.save(update_fields=['receipt_number'])

        if not invoice.gepg_approval:
            invoice.gepg_approval = reconcile.data.get('receipt_number', '')
            invoice.save(update_fields=['gepg_approval', 'updated_at'])

        if invoice.is_fully_paid:
            invoice.status = Invoice.Status.PAID
            invoice.paid_at = timezone.now()
            invoice.save(update_fields=['status', 'paid_at', 'updated_at'])

            application = invoice.application
            if application.status == Application.Status.PAYMENT_PENDING:
                application.transition_to(Application.Status.PAID, by=None, note=f'Invoice {invoice.control_number} settled')

    return payment, invoice.is_settled
