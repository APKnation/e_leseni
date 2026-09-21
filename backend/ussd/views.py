"""HTTP endpoint USSD gateways call (Africa's Talking style POST form data)."""
import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from integrations.models import IntegrationLog

from .menus import USSDHandler
from .models import USSDSession

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def gateway(request):
    """Single entry point for the USSD gateway.

    Expected POST fields: sessionId, phoneNumber, text (serviceCode optional).
    Returns text/plain body beginning with CON or END.
    """
    session_id = request.POST.get('sessionId') or request.POST.get('session_id') or ''
    phone = request.POST.get('phoneNumber') or request.POST.get('phone_number') or ''
    text = request.POST.get('text') or ''

    if not session_id or not phone:
        logger.warning('USSD gateway call missing fields: %s', dict(request.POST))
        return HttpResponse('END Invalid request.', content_type='text/plain', status=400)

    response_text = USSDHandler(session_id=session_id, phone=phone, text=text).handle()

    IntegrationLog.objects.create(
        system=IntegrationLog.System.USSD,
        direction=IntegrationLog.Direction.INBOUND,
        endpoint='ussd/gateway/',
        request_payload={'sessionId': session_id, 'phoneNumber': phone, 'text': text},
        response_payload={'response': response_text},
        status_code=200,
    )
    return HttpResponse(response_text, content_type='text/plain')
