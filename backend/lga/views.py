from django.db.models import Count
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import LGA, LicenceType, OfficerAssignment, Requirement, Ward
from .serializers import (
    LGASerializer,
    LicenceTypeSerializer,
    OfficerAssignmentSerializer,
    RequirementSerializer,
)


@api_view(['GET'])
@permission_classes([AllowAny])
def wards(request, lga_id):
    """Public list of wards for an LGA: /api/lgas/<id>/wards/"""
    lga = LGA.objects.filter(pk=lga_id).first()
    if lga is None:
        return Response({'detail': 'LGA not found.'}, status=404)
    return Response([
        {'id': w.id, 'name': w.name}
        for w in lga.wards.order_by('name')
    ])


@api_view(['GET'])
@permission_classes([AllowAny])
def regions(request):
    """Public list of regions that have LGAs registered in the system."""
    regions_ = (
        LGA.objects.values('region')
        .annotate(lga_count=Count('id'))
        .order_by('region')
    )
    return Response(list(regions_))


class PublicReadStaffWriteMixin:
    """AllowAnyone for GET/list; admin-only for writes."""

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]


class LGAViewSet(PublicReadStaffWriteMixin, viewsets.ReadOnlyModelViewSet):
    """Public reference data for LGAs, filterable by region (?region=...)."""

    queryset = LGA.objects.annotate(licence_type_count=Count('licence_types'))
    serializer_class = LGASerializer
    filterset_fields = ['region']
    search_fields = ['name', 'region', 'code']
    ordering = ['name']


class LicenceTypeViewSet(PublicReadStaffWriteMixin, viewsets.ReadOnlyModelViewSet):
    """Licence types, filterable by area and category:

    GET /api/licence-types/?lga=<id>&category=BUSINESS|DRIVING|GENERAL
    """

    queryset = LicenceType.objects.select_related('lga').prefetch_related('requirements')
    serializer_class = LicenceTypeSerializer
    filterset_fields = ['lga', 'category', 'requires_inspection']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']


class RequirementViewSet(PublicReadStaffWriteMixin, viewsets.ModelViewSet):
    """Requirements per licence type."""

    queryset = Requirement.objects.select_related('licence_type')
    serializer_class = RequirementSerializer
    filterset_fields = ['licence_type', 'kind', 'is_mandatory']


class OfficerAssignmentViewSet(viewsets.ModelViewSet):
    """Assign officers to licence types (admins only for writes)."""

    queryset = OfficerAssignment.objects.select_related('officer', 'licence_type')
    serializer_class = OfficerAssignmentSerializer
    filterset_fields = ['officer', 'licence_type', 'is_active']

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminUser()]
