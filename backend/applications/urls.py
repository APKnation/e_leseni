from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'applications', views.ApplicationViewSet, basename='application')
router.register(r'documents', views.ApplicationDocumentViewSet, basename='application-document')
router.register(r'inspections', views.InspectionViewSet, basename='inspection')

urlpatterns = [
    path('applications/<int:pk>/transition/', views.ApplicationTransitionView.as_view(), name='application-transition'),
    path('', include(router.urls)),
]
