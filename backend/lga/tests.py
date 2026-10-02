from django.test import TestCase

from accounts.models import User
from lga.models import LGA, LicenceType
from rest_framework import status
from rest_framework.test APIClient  # noqa: F401 (kept for future API tests)
