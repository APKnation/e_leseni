import secrets

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core_docs.validation import validate_pdf_document
from integrations.models import IntegrationLog

from .models import Business, BusinessDocument, BusinessLocation, TINApplication, TINApplicationDocument
from .serializers import (
    BusinessSerializer,
    BusinessDocumentSerializer,
    BusinessLocationSerializer,
    TINApplicationDocumentSerializer,
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
        user = self.request.user
        if not user.nida_number:
            raise exceptions.ValidationError(
                {'detail': 'Add your NIDA number to your profile before registering a business.'}
            )
        # Snapshot the owner's NIDA onto the business for the record.
        business = serializer.save(owner=user, nida_number=user.nida_number)
        self._auto_verify(business)

    def perform_update(self, serializer):
        business = serializer.save()
        self._auto_verify(business)

    def _auto_verify(self, business):
        """Verify TIN with TRA and registration with BRELA when the owner has a
        NIDA, the street ID letter is attached, and both numbers are present.
        Marks the business verified only if everything passes."""
        business.ensure_verified()

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify TIN with TRA and registration with BRELA via the adapters.

        Requires the owner's NIDA and a street identification letter — the same
        documents a real council asks for. Mock rules (dev): TIN 9-12 digits,
        BRELA numbers start with '1'.
        """
        business = self.get_object()
        if business.is_verified:
            return Response({'detail': 'Business is already verified.', 'is_verified': True})
        if not business.owner.nida_number:
            return Response(
                {'detail': 'The business owner must have a NIDA number on their profile before verification.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not business.documents.filter(kind=BusinessDocument.Kinds.STREET_ID_LETTER).exists():
            return Response(
                {'detail': 'Upload the street identification letter before verification.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not business.tin_number or not business.brela_registration_number:
            return Response(
                {'detail': 'Set tin_number and brela_registration_number before verifying.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from integrations.adapters import BRELAdapter, TRAAdapter

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

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_document(self, request, pk=None):
        """POST multipart {file, kind?} to attach any supporting document.

        Real councils expect PDF scans of the TIN certificate, BRELA
        certificate, lease agreement etc. Only PDF is accepted.
        """
        business = self.get_object()
        file = request.FILES.get('file')
        if file is None:
            return Response({'detail': 'A file is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_pdf_document(file)
        except DjangoValidationError as exc:
            return Response({'detail': '; '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        kind = (request.data.get('kind') or BusinessDocument.Kinds.OTHER).strip()
        if kind not in BusinessDocument.Kinds.values:
            return Response(
                {'detail': f'Unknown document kind "{kind}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = BusinessDocument.objects.create(business=business, kind=kind, file=file)
        return Response(
            BusinessDocumentSerializer(document, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


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

    @action(detail=False, methods=['post'], url_path='demo/apply-tin',
            parser_classes=[MultiPartParser, FormParser])
    def demo_apply_tin(self, request):
        """DEMO: apply for a TIN at TRA.

        Mirrors the real TRA ITAX form: the taxpayer's NIDA number and a PDF
        copy of the national ID must accompany the application. Creates a
        TINApplication that starts PENDING and is approved a moment later
        (async mock), then returns the TIN. 9 digits, so it passes the mock
        TRA verifier.
        """
        business_name = (request.data.get('business_name') or '').strip()
        taxpayer_name = (request.data.get('taxpayer_name') or '').strip()
        nida_number = (
            request.data.get('nida_number') or request.user.nida_number or ''
        ).strip()
        nida_copy = request.FILES.get('nida_copy')

        if not business_name or not taxpayer_name:
            return Response({'detail': 'business_name and taxpayer_name are required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not nida_number:
            return Response(
                {'detail': 'nida_number is required — TRA issues TINs against a national ID. '
                           'Add it to your profile or send it with the application.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not nida_copy:
            return Response(
                {'detail': 'A PDF copy of the national ID (nida_copy) is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_pdf_document(nida_copy)
        except DjangoValidationError as exc:
            return Response({'detail': '; '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        application = TINApplication.objects.create(
            applicant=request.user,
            business_name=business_name,
            taxpayer_name=taxpayer_name,
            nida_number=nida_number,
        )
        TINApplicationDocument.objects.create(
            tin_application=application,
            kind=TINApplicationDocument.Kinds.NIDA_COPY,
            file=nida_copy,
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
            request_payload={
                'business_name': business_name,
                'taxpayer_name': taxpayer_name,
                'nida_number': nida_number,
            },
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

    @action(detail=True, methods=['post'], url_path='street-id-letter',
            parser_classes=[MultiPartParser, FormParser])
    def street_id_letter(self, request, pk=None):
        """Upload the street identification letter for a business.

        POST multipart {file} — PDF only. The letter (from the street/mtaa
        chairman) confirms the business operates at the stated location and
        carries the owner's NIDA number.
        """
        business = self.get_object()
        file = request.FILES.get('file')
        if file is None:
            return Response({'detail': 'A file is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_pdf_document(file)
        except DjangoValidationError as exc:
            return Response({'detail': '; '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        document = BusinessDocument.objects.create(
            business=business,
            kind=BusinessDocument.Kinds.STREET_ID_LETTER,
            file=file,
        )
        return Response(
            BusinessDocumentSerializer(document, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class TINApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    """TRA TIN applications owned by the logged-in user."""

    serializer_class = TINApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TINApplication.objects.prefetch_related('documents')
        if self.request.user.is_lga_staff:
            return qs
        return qs.filter(applicant=self.request.user)

    @action(detail=True, methods=['post'], url_path='documents',
            parser_classes=[MultiPartParser, FormParser])
    def documents(self, request, pk=None):
        """POST multipart {file, kind?} to attach documents to a TIN application.

        Real TRA keeps the NIDA copy with the application; extra scans can be
        attached here. PDF only.
        """
        application = self.get_object()
        file = request.FILES.get('file')
        if file is None:
            return Response({'detail': 'A file is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_pdf_document(file)
        except DjangoValidationError as exc:
            return Response({'detail': '; '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        kind = (request.data.get('kind') or TINApplicationDocument.Kinds.OTHER).strip()
        if kind not in TINApplicationDocument.Kinds.values:
            return Response(
                {'detail': f'Unknown document kind "{kind}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        document = TINApplicationDocument.objects.create(
            tin_application=application, kind=kind, file=file
        )
        return Response(
            TINApplicationDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )


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
