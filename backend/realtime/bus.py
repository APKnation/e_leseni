"""In-process pub/sub hub for Server-Sent Events.

Every event is published to one or more *audience keys*:

- ``user:{id}``       the applicant who owns the application
- ``staff:{lga_id}``  LGA staff (officers, inspectors, approvers) of an LGA
- ``staff:all``       admins/superusers (see everything)

A subscriber registers a ``queue.Queue``; the SSE view drains it. This keeps
the whole feature self-contained with no external broker (Redis etc.) —
appropriate for the single-process demo deployment. Swap for Redis pub/sub
when running multiple workers.
"""
import threading

from django.utils import timezone

from applications.models import Application

_lock = threading.Lock()
_subscribers = {}  # queue.Queue -> set of audience keys


def subscribe(*keys):
    """Register a queue for the given audience keys. Returns (queue, unsubscribe)."""
    import queue

    q = queue.Queue(maxsize=100)
    with _lock:
        _subscribers[q] = set(keys)
    return q, lambda: unsubscribe(q)


def unsubscribe(q):
    with _lock:
        _subscribers.pop(q, None)


def publish(keys, event, data):
    """Push an event to every subscriber listening on any of ``keys``."""
    with _lock:
        targets = [q for q, ks in _subscribers.items() if ks.intersection(keys)]
    for q in targets:
        try:
            q.put_nowait({'event': event, 'data': data})
        except Exception:  # noqa: BLE001 - a slow consumer must not break others
            unsubscribe(q)


# -- Event builders --------------------------------------------------------


def _status_label(status):
    return Application.Status(status).label if status in Application.Status.values else status


def application_status(application, old_status, new_status, changed_by=None):
    """Publish an application status change to applicant + staff audiences."""
    keys = [f'user:{application.applicant_id}']
    lga_id = application.licence_type.lga_id
    if application.applicant.is_lga_staff:
        keys.append(f'staff:{lga_id}')
    if application.applicant.is_superuser or application.applicant.role == 'ADMIN':
        keys.append('staff:all')
    keys.extend(['staff:' + str(lga_id), 'staff:all'])

    publish(
        keys,
        'application.status',
        {
            'application_id': application.id,
            'reference_number': application.reference_number,
            'business_name': application.business.name,
            'licence_type_name': application.licence_type.name,
            'from_status': old_status,
            'to_status': new_status,
            'to_status_label': _status_label(new_status),
            'changed_by': (changed_by.get_full_name() or changed_by.username) if changed_by else 'System',
            'at': timezone.now().isoformat(),
        },
    )


def inspection_updated(inspection, action):
    """Publish inspection scheduling/conduction events to both audiences."""
    application = inspection.application
    publish(
        [f'user:{application.applicant_id}', f'staff:{application.licence_type.lga_id}', 'staff:all'],
        'inspection.update',
        {
            'application_id': application.id,
            'reference_number': application.reference_number,
            'inspection_id': inspection.id,
            'action': action,  # 'scheduled' | 'conducted' | 'updated'
            'scheduled_for': inspection.scheduled_for.isoformat(),
            'passed': inspection.passed,
            'at': timezone.now().isoformat(),
        },
    )
