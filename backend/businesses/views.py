import secrets

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from integrations.adapters import BRELAdapter, TRAAdapter
from integrations.models import IntegrationLog

from .models import Business, BusinessDocument, BusinessLocation, TINApplication
from .serializers import (
    BusinessSerializer,
    BusinessDocumentSerializer,
    BusinessLocationSerializer,
    TINApplicationSerializer,
)


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
        business = serializer.save(owner=self.request.user)
        self._auto_verify(business)

    def perform_update(self, serializer):
        business = serializer.save()
        self._auto_verify(business)

    def _auto_verify(self, business):
        """Verify TIN with TRA and registration with BRELA when both numbers
        are present (mock adapters in dev; real HTTP in production).
        Marks the business verified only if both pass."""
        if business.is_verified or not business.tin_number or not business.brela_registration_number:
            return
        tin_result = TRAAdapter().verify_tin(business.tin_number, business.name)
        brela_result = BRELAdapter().verify_registration(
            business.brela_registration_number, business.name
        )
        verified = (
            tin_result.success and tin_result.data.get('valid') is True
            and brela_result.success and brela_result.data.get('registered') is True
        )
        if verified:
            business.is_verified = True
            business.save(update_fields=['is_verified', 'updated_at'])

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


    @action(detail=False, methods=['post'], url_path='demo/brela-register')
    def demo_brela_register(self, request):
        """DEMO: register a business with BRELA and get a registration number.

        Stands in for the real BRELA ORES form. Returns a number starting with
        '1', which is exactly what the mock BRELA verifier accepts.
        """
        name = (request.data.get('business_name') or '').strip()
        if not name:
            return Response({'detail': 'business_name is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        registration_number = f'1{secrets.randbelow(10**8):08d}'
        payload = {
            'registered': True,
            'registration_number': registration_number,
            'entity_name': name,
            'status': 'ACTIVE',
            'source': 'BRELA (demo ORES)',
        }
        IntegrationLog.objects.create(
            system=IntegrationLog.System.BRELA,
            direction=IntegrationLog.Direction.OUTBOUND,
            endpoint='demo/brela-register/',
            request_payload={'business_name': name},
            response_payload=payload,
            status_code=200,
            is_success=True,
        )
        return Response(payload)

    @action(detail=False, methods=['post'], url_path='demo/apply-tin')
    def demo_apply_tin(self, request):
        """DEMO: apply for a TIN at TRA.

        Creates a TINApplication that starts PENDING and is approved a moment
        later (async mock), then returns the TIN. 9 digits, so it passes the
        mock TRA verifier.
        """
        business_name = (request.data.get('business_name') or '').strip()
        taxpayer_name = (request.data.get('taxpayer_name') or '').strip()
        if not business_name or not taxpayer_name:
            return Response({'detail': 'business_name and taxpayer_name are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        application = TINApplication.objects.create(
            applicant=request.user,
            business_name=business_name,
            taxpayer_name=taxpayer_name,
        )
        # Simulate TRA processing the request asynchronously.
        application.status = TINApplication.Status.APPROVED
        application.tin_number = f'{secrets.randbelow(10**9):09d}'
        application.processed_at = timezone.now()
        application.save(update_fields=['status', 'tin_number', 'processed_at'])

        IntegrationLog.objects.create(
            system=IntegrationLog.System.TRA,
            direction=IntegrationLog.Direction.OUTBOUND,
            endpoint='demo/apply-tin/',
            request_payload={'business_name': business_name, 'taxpayer_name': taxpayer_name},
            response_payload={'tin_number': application.tin_number, 'status': application.status},
            status_code=200,
            is_success=True,
        )
        serializer = TINApplicationSerializer(application)
        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        response['Location'] = f'/api/businesses/tin-applications/{application.id}/'
        return response

    @action(detail=False, methods=['get'], url_path='tin-applications')
    def tin_applications(self, request):
        """List the caller's TRA TIN applications (newest first)."""
        qs = TINApplication.objects.filter(applicant=request.user)[:20]
        serializer = TINApplicationSerializer(qs, many=True)
        return Response(serializer.data)


class TINApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    """TRA TIN applications owned by the logged-in user."""

    serializer_class = TINApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TINApplication.objects.filter(applicant=self.request.user)


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
