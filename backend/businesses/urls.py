from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'businesses', views.BusinessViewSet, basename='business')
router.register(r'business-documents', views.BusinessDocumentViewSet, basename='business-document')

urlpatterns = [
    path('', include(router.urls)),
]
