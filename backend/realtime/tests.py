"""Tests for the realtime event bus and SSE stream."""
import json
import queue as queuelib

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.state import token_backend

from accounts.models import User
from applications.models import Application
from businesses.models import Business, BusinessLocation
from lga.models import LGA, LicenceType
from realtime import bus


class BusSubscriptionTests(TestCase):
    def test_publish_reaches_matching_audience_only(self):
        q_hit, _ = bus.subscribe('user:1')
        q_miss, _ = bus.subscribe('user:2')

        bus.publish(['user:1'], 'application.status', {'hello': 1})

        self.assertEqual(q_hit.get_nowait()['data'], {'hello': 1})
        with self.assertRaises(queuelib.Empty):
            q_miss.get_nowait()

    def test_unsubscribe_stops_delivery(self):
        q, cancel = bus.subscribe('user:1')
        cancel()
        bus.publish(['user:1'], 'application.status', {'x': 1})
        with self.assertRaises(queuelib.Empty):
            q.get_nowait()


class StatusChangeEventTests(TestCase):
    """A transition publishes to applicant + staff audiences."""

    def setUp(self):
        self.lga = LGA.objects.create(name='Ilala', region='Dar', code='DS-IL')
        self.applicant = User.objects.create_user(username='app1', password='x' * 12)
        self.licence = LicenceType.objects.create(name='Food', code='FOOD-RT', fee=1, lga=self.lga)
        self.business = Business.objects.create(owner=self.applicant, name='Biz')
        self.location = BusinessLocation.objects.create(
            business=self.business, lga=self.lga, ward='W', street='S'
        )
        self.application = Application.objects.create(
            applicant=self.applicant, business=self.business,
            licence_type=self.licence, location=self.location,
        )

    def test_transition_publishes_event(self):
        q, _ = bus.subscribe(f'user:{self.applicant.id}', f'staff:{self.lga.id}', 'staff:all')
        with self.captureOnCommitCallbacks(execute=True):
            self.application.transition_to(Application.Status.SUBMITTED)
        event = q.get(timeout=1)
        self.assertEqual(event['event'], 'application.status')
        self.assertEqual(event['data']['to_status'], 'SUBMITTED')
        self.assertEqual(event['data']['reference_number'], self.application.reference_number)


class EventStreamAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='sse1', password='x' * 12)

    def test_missing_token_returns_401_event(self):
        response = self.client.get('/api/events/')
        self.assertEqual(response.status_code, 401)

    def test_bad_token_returns_401(self):
        response = self.client.get('/api/events/?token=not-a-jwt')
        self.assertEqual(response.status_code, 401)

    def test_valid_token_opens_stream(self):
        token = token_backend.encode({'user_id': self.user.id})
        response = self.client.get(f'/api/events/?token={token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        # The stream starts with a hello event.
        first_chunk = next(response.streaming_content)
        self.assertIn('event: hello', first_chunk.decode())

    def test_browser_accept_header_is_accepted(self):
        """Regression: EventSource sends Accept: text/event-stream; DRF
        content negotiation must not answer 406 Not Acceptable."""
        token = token_backend.encode({'user_id': self.user.id})
        response = self.client.get(
            f'/api/events/?token={token}', HTTP_ACCEPT='text/event-stream'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
