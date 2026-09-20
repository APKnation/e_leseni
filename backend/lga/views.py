from rest_framework import permissions, viewsets

from .models import LGA, LicenceType, OfficerAssignment, Requirement
from .serializers import (
    LGASerializer,
    LicenceTypeSerializer,
    OfficerAssignmentSerializer,
    RequirementSerializer,
)


class LGAViewSet(viewsets.ReadOnlyModelViewSet):
    """Public reference data for LGAs."""

    queryset = LGA.objects.all()
    serializer_class = LGASerializer
    filterset_fields = ['region']
    search_fields = ['name', 'region', 'code']


class LicenceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Licence types offered by LGAs, including their requirements."""

    queryset = LicenceType.objects.select_related('lga').prefetch_related('requirements')
    serializer_class = LicenceTypeSerializer
    filterset_fields = ['lga', 'requires_inspection']
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
