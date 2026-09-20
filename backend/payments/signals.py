"""Hooks into the application status flow.

When an application reaches PAYMENT_PENDING, an invoice is created
automatically (idempotent) and a control number is requested from GePG.
"""
import logging

from django.db import transaction
from django.dispatch import receiver

from applications.models import Application, application_status_changed

from . import services
from .models import Invoice

logger = logging.getLogger(__name__)


@receiver(application_status_changed, dispatch_uid='payments.create_invoice_on_payment_pending')
def create_invoice_on_payment_pending(sender, application, old_status, new_status, changed_by, **kwargs):
    """Auto-create the invoice (and request its control number) on PAYMENT_PENDING."""
    if new_status != Application.Status.PAYMENT_PENDING:
        return

    def _create_and_request():
        invoice, created = services.create_invoice_for_application(application)
        if created or invoice.status == Invoice.Status.PENDING:
            updated_invoice, requested = services.request_control_number(invoice)
            if requested:
                logger.info(
                    'Control number %s issued for %s',
                    updated_invoice.control_number, application.reference_number,
                )

    # Run after the originating transition's transaction commits.
    transaction.on_commit(_create_and_request)
