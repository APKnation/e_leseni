"""SMS sender abstraction.

Choose a backend with settings.SMS_BACKEND:
    'console'  - log to console/stdout and mark sent (default, dev)
    'database' - queue as QUEUED without sending (offline/testing)
    a dotted path - e.g. 'myapp.sms.AfricaIsTalkingBackend' for production
"""
import logging

from django.conf import settings
from django.utils import timezone

from .models import SMSLog

logger = logging.getLogger(__name__)


class BaseSMSBackend:
    """Send via an external gateway; subclass and implement send_message."""

    name = 'base'

    def send(self, sms_log):
        provider_id = self.send_message(sms_log.recipient, sms_log.body)
        sms_log.status = SMSLog.Status.SENT
        sms_log.provider_message_id = provider_id or ''
        sms_log.sent_at = timezone.now()
        sms_log.save(update_fields=['status', 'provider_message_id', 'sent_at'])
        return sms_log

    def send_message(self, recipient, body):
        """Return the provider message id (or ''). Must raise on failure."""
        raise NotImplementedError


class ConsoleSMSBackend(BaseSMSBackend):
    """Dev backend: print to the runserver console and mark sent."""

    name = 'console'

    def send(self, sms_log):
        logger.info('[SMS -> %s] %s', sms_log.recipient, sms_log.body)
        print(f'[SMS -> {sms_log.recipient}] {sms_log.body}')
        sms_log.status = SMSLog.Status.SENT
        sms_log.sent_at = timezone.now()
        sms_log.save(update_fields=['status', 'sent_at'])
        return sms_log


class DatabaseSMSBackend(BaseSMSBackend):
    """Queue-only backend: leaves entries QUEUED (e.g. for a Celery worker)."""

    name = 'database'

    def send(self, sms_log):
        return sms_log  # stays QUEUED


def get_sms_backend():
    path = getattr(settings, 'SMS_BACKEND', 'console')
    if path == 'console':
        return ConsoleSMSBackend()
    if path == 'database':
        return DatabaseSMSBackend()
    # Dotted import path
    from django.utils.module_loading import import_string

    return import_string(path)()


def send_sms(recipient, body, *, purpose=SMSLog.Purpose.GENERAL, user=None, application=None):
    """Create an SMSLog entry and attempt delivery via the configured backend.

    Never raises - delivery problems are recorded on the log entry so the
    signal chain (payments, licences) can't be broken by an SMS failure.
    """
    sms_log = SMSLog.objects.create(
        recipient=recipient, body=body, purpose=purpose, user=user, application=application,
        backend=getattr(settings, 'SMS_BACKEND', 'console'),
    )
    try:
        return get_sms_backend().send(sms_log)
    except Exception as exc:  # noqa: BLE001 - SMS must never break the flow
        sms_log.status = SMSLog.Status.FAILED
        sms_log.error_message = str(exc)[:500]
        sms_log.save(update_fields=['status', 'error_message'])
        logger.error('SMS to %s failed: %s', recipient, exc)
        return sms_log
