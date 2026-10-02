from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'lgas', views.LGAViewSet, basename='lga')
router.register(r'licence-types', views.LicenceTypeViewSet, basename='licence-type')
router.register(r'requirements', views.RequirementViewSet, basename='requirement')
router.register(r'officer-assignments', views.OfficerAssignmentViewSet, basename='officer-assignment')

urlpatterns = [
    path('regions/', views.regions, name='regions'),
    path('business-activities/', views.business_activities, name='business-activities'),
    path('lgas/<int:lga_id>/wards/', views.wards, name='lga-wards'),
    path('', include(router.urls)),
]
