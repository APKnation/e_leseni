from rest_framework import viewsets

from .models import Business, BusinessDocument, BusinessLocation
from .serializers import BusinessSerializer, BusinessDocumentSerializer, BusinessLocationSerializer


class BusinessViewSet(viewsets.ModelViewSet):
    """Businesses owned by the logged-in applicant (staff see all)."""

    serializer_class = BusinessSerializer
    filterset_fields = ['is_verified', 'sector']
    search_fields = ['name', 'tin_number', 'brela_registration_number']

    def get_queryset(self):
        qs = Business.objects.prefetch_related('locations', 'documents')
        user = self.request.user
        if user.is_authenticated and user.is_lga_staff:
            return qs
        return qs.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BusinessDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessDocumentSerializer
    filterset_fields = ['business', 'kind']

    def get_queryset(self):
        qs = BusinessDocument.objects.select_related('business')
        user = self.request.user
        if user.is_authenticated and user.is_lga_staff:
            return qs
        return qs.filter(business__owner=user)


class BusinessLocationViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessLocationSerializer
    filterset_fields = ['business', 'lga', 'is_primary']

    def get_queryset(self):
        qs = BusinessLocation.objects.select_related('business', 'lga')
        user = self.request.user
        if user.is_authenticated and user.is_lga_staff:
            return qs
        return qs.filter(business__owner=user)
