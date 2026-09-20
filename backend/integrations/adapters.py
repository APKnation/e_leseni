"""Adapters for external government systems.

Each adapter wraps an HTTP client, logs every call to IntegrationLog, and
exposes a small, typed surface for the rest of the codebase. Point the base
URLs at the mock endpoints in this app for development, or at the real
systems in production via settings.INTEGRATIONS.
"""
import logging
import uuid
from dataclasses import dataclass, field

import requests
from django.conf import settings

from .models import IntegrationLog

logger = logging.getLogger(__name__)


@dataclass
class AdapterResult:
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ''


class BaseAdapter:
    """HTTP client wrapper with integration logging."""

    system = 'UNKNOWN'

    def __init__(self, base_url=None, timeout=10):
        self.base_url = (base_url or self._default_base_url()).rstrip('/')
        self.timeout = timeout

    def _default_base_url(self):
        return settings.INTEGRATIONS.get(f'{self.system}_BASE_URL', '')

    def _post(self, path, payload):
        url = f'{self.base_url}/{path.lstrip("/")}'
        log = IntegrationLog(
            system=self.system, direction=IntegrationLog.Direction.OUTBOUND, endpoint=url,
            request_payload=payload,
        )
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            log.status_code = response.status_code
            try:
                log.response_payload = response.json()
            except ValueError:
                log.response_payload = {'raw': response.text[:2000]}
            log.is_success = response.status_code < 400
            if not log.is_success:
                log.error_message = f'HTTP {response.status_code}'
            response.raise_for_status()
            return AdapterResult(success=True, data=log.response_payload or {})
        except requests.RequestException as exc:
            log.is_success = False
            log.error_message = str(exc)[:500]
            logger.warning('%s call failed: %s', self.system, exc)
            return AdapterResult(success=False, error=log.error_message)
        finally:
            log.save()


class BRELAdapter(BaseAdapter):
    """Business Registrations and Licensing Agency - name/registration checks."""

    system = 'BRELA'

    def verify_registration(self, registration_number, business_name):
        return self._post('verify/', {
            'registration_number': registration_number,
            'business_name': business_name,
        })


class TRAAdapter(BaseAdapter):
    """Tanzania Revenue Authority - TIN verification."""

    system = 'TRA'

    def verify_tin(self, tin_number, taxpayer_name):
        return self._post('verify-tin/', {
            'tin_number': tin_number,
            'taxpayer_name': taxpayer_name,
        })


class GePGAdapter(BaseAdapter):
    """Government Electronic Payment Gateway - control numbers and receipts."""

    system = 'GEPG'

    def request_control_number(self, bill_amount, bill_reference, payer_name, description):
        return self._post('bill/', {
            'bill_amount': str(bill_amount),
            'bill_reference': bill_reference,
            'payer_name': payer_name,
            'bill_description': description,
        })

    def reconcile_payment(self, control_number, amount_paid):
        return self._post('reconcile/', {
            'control_number': control_number,
            'amount_paid': str(amount_paid),
        })
