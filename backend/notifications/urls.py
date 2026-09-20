from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'sms-logs', views.SMSLogViewSet, basename='sms-log')

urlpatterns = [
    path('', include(router.urls)),
]
