"""Licence services: issuance on PAID, QR payloads, renewal helpers."""
import logging

from django.utils import timezone

from applications.models import Application

from .models import Licence

logger = logging.getLogger(__name__)


def issue_licence_for_application(application):
    """Issue a licence for a PAID application. Idempotent.

    Called by the signal receiver when an application reaches PAID.
    """
    if getattr(application, 'licence', None):
        return application.licence, False

    licence = Licence.objects.create(
        application=application,
        business_name=application.business.name,
        holder=application.applicant,
        licence_type=application.licence_type,
        lga=application.licence_type.lga,
        valid_until=timezone.now().date()
        + timezone.timedelta(days=30 * application.licence_type.validity_months),
    )
    logger.info('Licence %s issued for %s', licence.licence_number, application.reference_number)
    return licence, True


def build_qr_payload(licence):
    """The payload encoded in the licence QR code.

    Verification hits /api/licences/verify/{token}/ - officers scan this
    with any QR reader that opens URLs.
    """
    return f'/api/licences/verify/{licence.qr_token}/'
