from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'licences', views.LicenceViewSet, basename='licence')
router.register(r'renewals', views.RenewalViewSet, basename='renewal')

urlpatterns = [
    path('licences/verify/<str:token>/', views.verify_licence, name='licence-verify'),
    path('', include(router.urls)),
]
