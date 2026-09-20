"""Adapters for external government systems.

Each adapter wraps an HTTP client, logs every call to IntegrationLog, and
exposes a small, typed surface for the rest of the codebase.

When the configured base URL points at this same Django process (localhost),
the call is dispatched in-process via Django's request handler instead of a
network hop - so the mock endpoints in this app work without running a second
server. Point the base URLs at the real systems in production to get real HTTP.
"""
import json
import logging
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import requests
from django.conf import settings

from .models import IntegrationLog

logger = logging.getLogger(__name__)

# Hosts that mean "the mock endpoints hosted by this very process".
LOCAL_MOCK_HOSTS = {'localhost', '127.0.0.1', '0.0.0.0', 'testserver'}


@dataclass
class AdapterResult:
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ''


class BaseAdapter:
    """HTTP client wrapper with integration logging and in-process mock support."""

    system = 'UNKNOWN'

    def __init__(self, base_url=None, timeout=10):
        self.base_url = (base_url or self._default_base_url()).rstrip('/')
        self.timeout = timeout

    def _default_base_url(self):
        return settings.INTEGRATIONS.get(f'{self.system}_BASE_URL', '')

    def _build_url(self, path):
        return f'{self.base_url}/{path.lstrip("/")}'

    def _call_direct(self, path, payload):
        """POST to our own mock endpoint in-process (no network)."""
        from django.test import Client

        parts = urlsplit(self._build_url(path))
        client = Client()
        response = client.post(parts.path, data=json.dumps(payload), content_type='application/json')
        try:
            data = json.loads(response.content)
        except (ValueError, UnicodeDecodeError):
            data = {'raw': response.content[:2000].decode(errors='replace')}
        return response.status_code, data

    def _call_http(self, path, payload):
        """POST to a real external endpoint over the network."""
        url = self._build_url(path)
        response = requests.post(url, json=payload, timeout=self.timeout)
        try:
            data = response.json()
        except ValueError:
            data = {'raw': response.text[:2000]}
        return response.status_code, data

    def _post(self, path, payload):
        url = self._build_url(path)
        host = urlsplit(url).hostname or ''
        use_direct = host in LOCAL_MOCK_HOSTS and not getattr(settings, 'INTEGRATIONS_FORCE_HTTP', False)

        log = IntegrationLog(
            system=self.system, direction=IntegrationLog.Direction.OUTBOUND,
            endpoint=url, request_payload=payload,
        )
        try:
            if use_direct:
                status_code, data = self._call_direct(path, payload)
            else:
                status_code, data = self._call_http(path, payload)

            log.status_code = status_code
            log.response_payload = data
            log.is_success = status_code < 400
            if not log.is_success:
                log.error_message = f'HTTP {status_code}'
            return AdapterResult(success=log.is_success, data=data)
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
