"""Mock government endpoints for development and testing.

These views emulate BRELA, TRA and GePG well enough for the whole e-Leseni
flow to run end-to-end without the real systems. Swap the base URLs in
settings.INTEGRATIONS to move to production.
"""
import logging
import uuid

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .adapters import AdapterResult
from .models import IntegrationLog

logger = logging.getLogger(__name__)


def _mock_log(system, endpoint, request_data, response_data):
    """Record the mock's response the same way outbound calls are logged."""
    IntegrationLog.objects.create(
        system=system, direction=IntegrationLog.Direction.INBOUND, endpoint=endpoint,
        request_payload=request_data, response_payload=response_data, status_code=200,
    )


@api_view(['POST'])
@permission_classes([])
def mock_brela_verify(request):
    """Verify a BRELA registration number.

    Mock rule: numbers starting with '1' are registered; anything else is not.
    """
    registration_number = (request.data.get('registration_number') or '').strip()
    response_data = {
        'registered': bool(registration_number.startswith('1')),
        'registration_number': registration_number,
        'entity_name': request.data.get('business_name', ''),
        'status': 'ACTIVE' if registration_number.startswith('1') else 'NOT_FOUND',
    }
    _mock_log(IntegrationLog.System.BRELA, 'mock/brela/verify/', request.data, response_data)
    return Response(response_data)


@api_view(['POST'])
@permission_classes([])
def mock_tra_verify_tin(request):
    """Verify a TRA TIN. Mock rule: valid if 9-12 digits."""
    tin = (request.data.get('tin_number') or '').strip()
    is_valid = tin.isdigit() and 9 <= len(tin) <= 12
    response_data = {
        'valid': is_valid,
        'tin_number': tin,
        'taxpayer_name': request.data.get('taxpayer_name', '') if is_valid else '',
    }
    _mock_log(IntegrationLog.System.TRA, 'mock/tra/verify-tin/', request.data, response_data)
    return Response(response_data)


@api_view(['POST'])
@permission_classes([])
def mock_gepg_bill(request):
    """Issue a control number for a bill.

    Mock rule: control numbers start with 99 and reference the bill id.
    """
    bill_reference = request.data.get('bill_reference') or f'BILL-{uuid.uuid4().hex[:10].upper()}'
    response_data = {
        'bill_id': f'GEPG-{uuid.uuid4().hex[:12].upper()}',
        'control_number': f'99{uuid.uuid4().hex[:8].upper()}',
        'bill_reference': bill_reference,
        'bill_amount': request.data.get('bill_amount', '0'),
        'bill_status': 'ISSUED',
        'expiry_date': '2099-12-31',
    }
    _mock_log(IntegrationLog.System.GEPG, 'mock/gepg/bill/', request.data, response_data)
    return Response(response_data)


@api_view(['POST'])
@permission_classes([])
def mock_gepg_reconcile(request):
    """Confirm a payment against a control number.

    Mock rule: any positive amount reconciles; return a receipt number.
    """
    control_number = (request.data.get('control_number') or '').strip()
    try:
        amount = float(request.data.get('amount_paid') or 0)
    except (TypeError, ValueError):
        amount = 0

    if not control_number or amount <= 0:
        response_data = {'receipt_number': '', 'payment_status': 'FAILED',
                         'reason': 'Invalid control number or non-positive amount'}
        code = status.HTTP_400_BAD_REQUEST
    else:
        response_data = {
            'receipt_number': f'RCP-{uuid.uuid4().hex[:10].upper()}',
            'control_number': control_number,
            'amount_paid': request.data.get('amount_paid'),
            'payment_status': 'SUCCESS',
            'paid_at': request.headers.get('X-Mock-Paid-At', ''),
        }
        code = status.HTTP_200_OK

    _mock_log(IntegrationLog.System.GEPG, 'mock/gepg/reconcile/', request.data, response_data)
    return Response(response_data, status=code)
