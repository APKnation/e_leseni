from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from lga.models import LGA

User = get_user_model()


class AdminUserCrudTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.lga = LGA.objects.create(name='Ilala Municipal Council', code='ILALA', region='Dar es Salaam')

        self.admin = User.objects.create_user(
            username='sysadmin',
            email='admin@example.com',
            password='AdminPassword123!',
            role=User.Roles.ADMIN,
        )

        self.officer = User.objects.create_user(
            username='officer1',
            email='officer@example.com',
            password='OfficerPassword123!',
            role=User.Roles.OFFICER,
            lga=self.lga,
        )

        self.applicant = User.objects.create_user(
            username='citizen1',
            email='citizen@example.com',
            password='CitizenPassword123!',
            role=User.Roles.APPLICANT,
        )

    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get('/api/users/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Results are paginated
        results = res.data.get('results', res.data)
        self.assertGreaterEqual(len(results), 3)

    def test_admin_can_create_inspector(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            'username': 'inspector_john',
            'first_name': 'John',
            'last_name': 'Mwita',
            'email': 'john.mwita@ilala.go.tz',
            'phone_number': '0754111222',
            'role': User.Roles.INSPECTOR,
            'lga': self.lga.id,
            'password': 'SecureInspectorPass123!',
        }
        res = self.client.post('/api/users/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['username'], 'inspector_john')
        self.assertEqual(res.data['role'], User.Roles.INSPECTOR)
        self.assertEqual(res.data['lga'], self.lga.id)

        created = User.objects.get(username='inspector_john')
        self.assertTrue(created.check_password('SecureInspectorPass123!'))
        self.assertEqual(created.role, User.Roles.INSPECTOR)
        self.assertTrue(created.is_lga_staff)

    def test_admin_can_create_approver(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            'username': 'approver_jane',
            'first_name': 'Jane',
            'last_name': 'Kavishe',
            'email': 'jane.kavishe@ilala.go.tz',
            'phone_number': '0714222333',
            'role': User.Roles.APPROVER,
            'lga': self.lga.id,
            'password': 'SecureApproverPass123!',
        }
        res = self.client.post('/api/users/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['role'], User.Roles.APPROVER)

    def test_non_admin_cannot_create_user(self):
        self.client.force_authenticate(user=self.officer)
        payload = {
            'username': 'sneaky_user',
            'email': 'sneaky@example.com',
            'password': 'Password123!',
            'role': User.Roles.INSPECTOR,
        }
        res = self.client.post('/api/users/', payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_user(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(f'/api/users/{self.officer.id}/', {
            'first_name': 'Amina',
            'last_name': 'Bakari',
            'phone_number': '0789000111',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.officer.refresh_from_db()
        self.assertEqual(self.officer.first_name, 'Amina')
        self.assertEqual(self.officer.phone_number, '0789000111')

    def test_admin_can_reset_user_password(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(f'/api/users/{self.officer.id}/reset-password/', {
            'new_password': 'BrandNewPassword999!',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.officer.refresh_from_db()
        self.assertTrue(self.officer.check_password('BrandNewPassword999!'))

    def test_admin_can_toggle_active_status(self):
        self.client.force_authenticate(user=self.admin)
        self.assertTrue(self.officer.is_active)
        res = self.client.post(f'/api/users/{self.officer.id}/toggle-active/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['is_active'])
        self.officer.refresh_from_db()
        self.assertFalse(self.officer.is_active)

        # Toggle back
        res = self.client.post(f'/api/users/{self.officer.id}/toggle-active/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_active'])
        self.officer.refresh_from_db()
        self.assertTrue(self.officer.is_active)

    def test_admin_cannot_deactivate_or_delete_self(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(f'/api/users/{self.admin.id}/toggle-active/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        del_res = self.client.delete(f'/api/users/{self.admin.id}/')
        self.assertEqual(del_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_delete_user(self):
        self.client.force_authenticate(user=self.admin)
        disposable = User.objects.create_user(username='disposable', password='Password123!')
        res = self.client.delete(f'/api/users/{disposable.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=disposable.id).exists())


class TokenRotationBlacklistTests(TestCase):
    """JWT session contract: rotation with blacklist.

    The web client silently refreshes on 401 and stores the rotated pair, so
    reusing an old refresh token must be rejected (BLACKLIST_AFTER_ROTATION)
    while the rotated one keeps working.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='rotator',
            email='rotator@example.com',
            password='RotatePassword123!',
            role=User.Roles.APPLICANT,
        )

    def _login(self):
        res = self.client.post('/api/auth/login/', {
            'username': 'rotator', 'password': 'RotatePassword123!',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return res.data

    def _refresh(self, token: str):
        return self.client.post('/api/auth/refresh/', {'refresh': token})

    def test_refresh_returns_rotated_pair(self):
        tokens = self._login()
        res = self._refresh(tokens['refresh'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # ROTATE_REFRESH_TOKENS: the backend hands back a new refresh too
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertNotEqual(res.data['refresh'], tokens['refresh'])

    def test_reused_old_refresh_token_is_blacklisted(self):
        tokens = self._login()
        old_refresh = tokens['refresh']
        first = self._refresh(old_refresh)
        self.assertEqual(first.status_code, status.HTTP_200_OK)

        # Replaying the already-rotated token is rejected (blacklisted)...
        replay = self._refresh(old_refresh)
        self.assertEqual(replay.status_code, status.HTTP_401_UNAUTHORIZED)

        # ...and the fresh pair still works.
        second = self._refresh(first.data['refresh'])
        self.assertEqual(second.status_code, status.HTTP_200_OK)

    def test_access_token_survives_refresh_rotation(self):
        """Rotation blacklists the old refresh token, never the access token."""
        tokens = self._login()
        self._refresh(tokens['refresh'])
        me = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data['username'], 'rotator')

