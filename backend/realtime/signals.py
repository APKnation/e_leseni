"""Signal receivers that publish realtime events for the licensing flow."""
import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from applications.models import Application, Inspection, application_status_changed

from . import bus

logger = logging.getLogger(__name__)


@receiver(application_status_changed, dispatch_uid='realtime.publish_status_change')
def publish_status_change(sender, application, old_status, new_status, changed_by, **kwargs):
    """Forward every status transition to the realtime bus after commit."""

    def _publish():
        try:
            bus.application_status(application, old_status, new_status, changed_by)
        except Exception:  # noqa: BLE001 - realtime must never break the flow
            logger.exception('Realtime publish failed for %s', application.reference_number)

    transaction.on_commit(_publish)


@receiver(post_save, sender=Inspection, dispatch_uid='realtime.publish_inspection')
def publish_inspection(sender, instance, created, **kwargs):
    """Publish inspection scheduled/conducted events after commit."""
    action = 'scheduled' if created else 'updated'
    if not created and instance.conducted_at and instance.passed is not None:
        action = 'conducted'

    def _publish():
        try:
            bus.inspection_updated(instance, action)
        except Exception:  # noqa: BLE001
            logger.exception('Realtime inspection publish failed for %s', instance.application_id)

    transaction.on_commit(_publish)
