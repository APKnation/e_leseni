"""Hooks into the application status flow: issue a licence on PAID."""
import logging

from django.db import transaction
from django.dispatch import receiver

from applications.models import Application, application_status_changed

from . import services

logger = logging.getLogger(__name__)


@receiver(application_status_changed, dispatch_uid='licences.issue_on_paid')
def issue_licence_on_paid(sender, application, old_status, new_status, changed_by, **kwargs):
    """Auto-issue the licence once an application is fully PAID."""
    if new_status != Application.Status.PAID:
        return

    transaction.on_commit(lambda: services.issue_licence_for_application(application))
