from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from integrations.adapters import BRELAdapter, TRAAdapter

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

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify TIN with TRA and registration with BRELA via the adapters.

        Mock rules (dev): TIN is 9-12 digits; BRELA numbers start with '1'.
        Marks the business verified only if both pass.
        """
        business = self.get_object()
        if business.is_verified:
            return Response({'detail': 'Business is already verified.', 'is_verified': True})
        if not business.tin_number or not business.brela_registration_number:
            return Response(
                {'detail': 'Set tin_number and brela_registration_number before verifying.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tin_result = TRAAdapter().verify_tin(business.tin_number, business.name)
        brela_result = BRELAdapter().verify_registration(
            business.brela_registration_number, business.name
        )
        verified = tin_result.success and tin_result.data.get('valid') is True and \
            brela_result.success and brela_result.data.get('registered') is True
        business.is_verified = verified
        business.save(update_fields=['is_verified', 'updated_at'])

        return Response({
            'is_verified': verified,
            'tra': {'success': tin_result.success, 'valid': tin_result.data.get('valid', False)},
            'brela': {'success': brela_result.success, 'registered': brela_result.data.get('registered', False)},
        })


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
