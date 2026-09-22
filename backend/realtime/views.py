"""Server-Sent Events stream for application progress.

GET /api/events/ (text/event-stream)

Auth: the browser's EventSource cannot send an Authorization header, so the
JWT access token is accepted as a ``?token=`` query parameter and validated
with the same SimpleJWT machinery used everywhere else. HTTPS-only in
production keeps the token in the URL acceptable; access tokens also expire
after 2 hours.
"""
import json
import logging
import queue as queuelib

from django.db import close_old_connections
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework.renderers import BaseRenderer
from rest_framework_simplejwt.state import token_backend
from rest_framework.views import APIView

from accounts.models import User
from applications.models import Application

from . import bus

logger = logging.getLogger(__name__)

HEARTBEAT_SECONDS = 15
SNAPSHOT_LIMIT = 50


class EventStreamRenderer(BaseRenderer):
    """Accept text/event-stream so DRF content negotiation passes for SSE."""

    media_type = 'text/event-stream'
    format = 'text'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class EventStreamView(APIView):
    """SSE stream of status changes relevant to the authenticated user."""

    authentication_classes = []  # custom token auth below (EventSource limitation)
    permission_classes = []
    renderer_classes = [EventStreamRenderer]  # accept text/event-stream

    def get(self, request):
        user = self._user_from_token(request)
        if user is None:
            return StreamingHttpResponse(
                _sse('error', {'detail': 'Authentication required (pass ?token=<JWT access token>).'}),
                content_type='text/event-stream',
                status=401,
            )

        audience = self._audience_for(user)
        q, cancel = bus.subscribe(*audience)

        response = StreamingHttpResponse(
            self._stream(user, q, cancel),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    # -- auth ----------------------------------------------------------------

    @staticmethod
    def _user_from_token(request):
        raw = request.query_params.get('token') or ''
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        if auth.lower().startswith('bearer '):
            raw = auth.split(' ', 1)[1]
        if not raw:
            return None
        try:
            payload = token_backend.decode(raw, verify=True)
        except Exception:  # noqa: BLE001 - TokenError does not wrap every PyJWT error
            return None
        try:
            return User.objects.get(pk=payload.get('user_id'), is_active=True)
        except (User.DoesNotExist, ValueError, TypeError):
            return None

    @staticmethod
    def _audience_for(user):
        if user.is_superuser or user.role == 'ADMIN':
            return ['staff:all']
        if user.is_lga_staff:
            return [f'staff:{user.lga_id}'] if user.lga_id else []
        return [f'user:{user.id}']

    # -- streaming -------------------------------------------------------------

    def _stream(self, user, q, cancel):
        try:
            yield _sse('hello', {'connected_at': timezone.now().isoformat(), 'user': user.username})
            yield from self._snapshot(user)

            while True:
                try:
                    event = q.get(timeout=HEARTBEAT_SECONDS)
                except queuelib.Empty:
                    yield _sse('ping', {'at': timezone.now().isoformat()})
                    close_old_connections()  # long-lived conn must not pin stale DB conns
                    continue
                yield _sse(event['event'], event['data'])
        except GeneratorExit:
            raise
        except Exception:  # noqa: BLE001 - log, client reconnects on close
            logger.exception('SSE stream crashed for %s', user.username)
        finally:
            cancel()

    def _snapshot(self, user):
        """Emit current state of the user's (or LGA's) applications on connect."""
        apps = Application.objects.select_related('business', 'licence_type', 'licence_type__lga')
        if user.is_superuser or user.role == 'ADMIN':
            pass
        elif user.is_lga_staff:
            apps = apps.filter(licence_type__lga_id=user.lga_id) if user.lga_id else apps.none()
        else:
            apps = apps.filter(applicant=user)
        for app in apps.order_by('-updated_at')[:SNAPSHOT_LIMIT]:
            yield _sse('application.status', {
                'application_id': app.id,
                'reference_number': app.reference_number,
                'business_name': app.business.name,
                'licence_type_name': app.licence_type.name,
                'from_status': None,
                'to_status': app.status,
                'to_status_label': Application.Status(app.status).label,
                'changed_by': 'Snapshot',
                'at': app.updated_at.isoformat(),
                'snapshot': True,
            })


def _sse(event, data):
    return f'event: {event}\ndata: {json.dumps(data, default=str)}\n\n'
