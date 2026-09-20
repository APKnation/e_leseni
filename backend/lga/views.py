from django.db.models import Count
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import LGA, LicenceType, OfficerAssignment, Requirement
from .serializers import (
    LGASerializer,
    LicenceTypeSerializer,
    OfficerAssignmentSerializer,
    RequirementSerializer,
)


@api_view(['GET'])
@permission_classes([AllowAny])
def regions(request):
    """Public list of all regions that have LGAs registered in the system."""
    regions_ = (
        LGA.objects.values('region')
        .annotate(lga_count=Count('id'))
        .order_by('region')
    )
    return Response(list(regions_))


class LGAViewSet(viewsets.ReadOnlyModelViewSet):
    """Public reference data for LGAs, filterable by region."""

    queryset = LGA.objects.annotate(licence_type_count=Count('licence_types'))
    serializer_class = LGASerializer
    filterset_fields = ['region']
    search_fields = ['name', 'region', 'code']


class LicenceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Licence types offered by LGAs, including their requirements."""

    queryset = LicenceType.objects.select_related('lga').prefetch_related('requirements')
    serializer_class = LicenceTypeSerializer
    filterset_fields = ['lga', 'category', 'requires_inspection']
    search_fields = ['name', 'code', 'description']


class RequirementViewSet(viewsets.ModelViewSet):
    """Requirements per licence type (staff-managed)."""

    queryset = Requirement.objects.select_related('licence_type')
    serializer_class = RequirementSerializer
    filterset_fields = ['licence_type', 'kind', 'is_mandatory']

    def get_permissions(self):
        if self.request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class OfficerAssignmentViewSet(viewsets.ModelViewSet):
    """Assign officers to licence types (admins only)."""

    queryset = OfficerAssignment.objects.select_related('officer', 'licence_type')
    serializer_class = OfficerAssignmentSerializer
    filterset_fields = ['officer', 'licence_type', 'is_active']

    def get_permissions(self):
        if self.request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
