"""Licence services: issuance on PAID, QR payloads, renewal helpers."""
import logging

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone

from applications.models import Application

from .models import Licence

logger = logging.getLogger(__name__)

# Frontend base URL used in QR codes. Set FRONTEND_URL in .env for a real
# deployment (e.g. https://leseni.go.tz); defaults to the Angular dev server.
FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'http://localhost:4200')


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
        + relativedelta(months=application.licence_type.validity_months),
    )
    logger.info('Licence %s issued for %s', licence.licence_number, application.reference_number)

    # Complete the status flow: PAID -> ISSUED (fires the issuance SMS).
    if application.status == Application.Status.PAID:
        application.transition_to(Application.Status.ISSUED, by=None,
                                  note=f'Licence {licence.licence_number} issued')
    return licence, True


def build_qr_payload(licence):
    """The payload encoded in the licence QR code.

    Opens the public verification page (Angular) which then calls
    /api/licences/verify/{token}/. Officers and anyone else can scan the QR
    with any phone and see a human-readable verification result.
    """
    return f'{FRONTEND_URL}/verify/{licence.qr_token}'
