"""SMS hooks into the application status flow.

Fires on: SUBMITTED, APPROVED, PAID (payment confirmed), ISSUED,
REJECTED and RETURNED_FOR_CORRECTION. Control-number SMS is sent by the
payments app once GePG issues it.
"""
import logging

from django.db import transaction
from django.dispatch import receiver

from applications.models import Application, application_status_changed

from . import services

logger = logging.getLogger(__name__)


def _applicant_phone(application):
    phone = (application.applicant.phone_number or '').strip()
    return phone or None


@receiver(application_status_changed, dispatch_uid='notifications.notify_on_status_change')
def notify_on_status_change(sender, application, old_status, new_status, changed_by, **kwargs):
    phone = _applicant_phone(application)
    if not phone:
        return  # no phone on file - skip silently

    def _send():
        try:
            if new_status == Application.Status.SUBMITTED:
                services.application_submitted(application, phone)
            elif new_status == Application.Status.APPROVED:
                services.application_approved(application, phone)
            elif new_status == Application.Status.PAID:
                invoice = getattr(application, 'invoice', None)
                services.payment_confirmed(
                    application, phone,
                    amount=invoice.amount if invoice else application.licence_type.fee,
                    currency=invoice.currency if invoice else 'TZS',
                    receipt=invoice.gepg_approval if invoice else '',
                )
            elif new_status == Application.Status.ISSUED:
                licence = getattr(application, 'licence', None)
                if licence:
                    services.licence_issued(application, phone, licence.licence_number, licence.valid_until)
            elif new_status == Application.Status.REJECTED:
                services.application_rejected(application, phone, reason=application.rejection_reason)
            elif new_status == Application.Status.RETURNED_FOR_CORRECTION:
                services.returned_for_correction(application, phone)
        except Exception:  # noqa: BLE001 - never break the status flow
            logger.exception('Notification failed for %s', application.reference_number)

    transaction.on_commit(_send)
