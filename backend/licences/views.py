from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import Licence, Renewal
from .serializers import LicenceSerializer, LicenceVerifySerializer, RenewalSerializer


class LicenceViewSet(viewsets.ReadOnlyModelViewSet):
    """Licences; applicants see their own, staff see all.

    Actions:
        GET /api/licences/{id}/qr/       - QR payload for printing
        POST /api/licences/{id}/renew/   - request a renewal
    """

    serializer_class = LicenceSerializer
    filterset_fields = ['status', 'lga', 'licence_type']
    search_fields = ['licence_number', 'business_name', 'holder__username']

    def get_queryset(self):
        qs = Licence.objects.select_related(
            'application', 'holder', 'licence_type', 'lga'
        ).prefetch_related('renewals')
        user = self.request.user
        if user.is_lga_staff:
            return qs
        return qs.filter(holder=user)

    @action(detail=True, methods=['get'])
    def qr(self, request, pk=None):
        licence = self.get_object()
        from .services import build_qr_payload

        return Response({'licence_number': licence.licence_number, 'qr_payload': build_qr_payload(licence)})

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        licence = self.get_object()
        if licence.status not in {Licence.Status.ACTIVE, Licence.Status.EXPIRED, Licence.Status.RENEWAL_PENDING}:
            return Response(
                {'detail': f'Licence cannot be renewed (status: {licence.status}).'},
                status=status.HTTP_409_CONFLICT,
            )
        if Renewal.objects.filter(licence=licence, status=Renewal.Status.PENDING).exists():
            return Response({'detail': 'A renewal is already pending for this licence.'}, status=status.HTTP_409_CONFLICT)

        renewal = Renewal.objects.create(licence=licence, requested_by=request.user)
        if licence.status == Licence.Status.ACTIVE:
            licence.status = Licence.Status.RENEWAL_PENDING
            licence.save(update_fields=['status', 'updated_at'])
        return Response(RenewalSerializer(renewal, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_licence(request, token):
    """Public endpoint scanned from the licence QR code."""
    licence = Licence.objects.filter(qr_token=token).select_related('licence_type', 'lga').first()
    if licence is None:
        return Response({'valid': False, 'detail': 'Licence not found.'}, status=status.HTTP_404_NOT_FOUND)

    data = {
        'valid': licence.status == Licence.Status.ACTIVE and not licence.is_expired,
        'licence_number': licence.licence_number,
        'business_name': licence.business_name,
        'licence_type': licence.licence_type.name,
        'lga': licence.lga.name,
        'status': licence.status,
        'valid_from': licence.valid_from,
        'valid_until': licence.valid_until,
        'is_expired': licence.is_expired,
        'checked_at': timezone.now(),
    }
    return Response(LicenceVerifySerializer(data).data)


class RenewalViewSet(viewsets.ReadOnlyModelViewSet):
    """Renewal requests; applicants see their own, staff see all.

    Staff action:
        POST /api/renewals/{id}/decide/  - approve or reject {\"decision\": \"approve|reject\"}
    """

    serializer_class = RenewalSerializer
    filterset_fields = ['status', 'licence']

    def get_queryset(self):
        qs = Renewal.objects.select_related('licence', 'requested_by')
        user = self.request.user
        if user.is_lga_staff:
            return qs
        return qs.filter(requested_by=user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def decide(self, request, pk=None):
        renewal = self.get_object()
        decision = (request.data.get('decision') or '').lower()
        if renewal.status != Renewal.Status.PENDING:
            return Response({'detail': 'Renewal has already been decided.'}, status=status.HTTP_409_CONFLICT)
        if decision not in {'approve', 'reject'}:
            return Response({'detail': 'decision must be "approve" or "reject".'}, status=status.HTTP_400_BAD_REQUEST)

        if decision == 'approve':
            renewal.status = Renewal.Status.APPROVED
            renewal.fee_paid = renewal.licence.licence_type.fee
            renewal.new_valid_until = renewal.licence.valid_until.replace(
                year=renewal.licence.valid_until.year + 1
            )
        else:
            renewal.status = Renewal.Status.REJECTED
            if renewal.licence.status == Licence.Status.RENEWAL_PENDING:
                renewal.licence.status = Licence.Status.ACTIVE
                renewal.licence.save(update_fields=['status', 'updated_at'])
        renewal.decided_at = timezone.now()
        renewal.save()
        return Response(RenewalSerializer(renewal, context={'request': request}).data)
