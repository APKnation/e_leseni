from django.db.models import Count, Prefetch, Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import LGA, LicenceType, BusinessActivity, OfficerAssignment, Requirement, Ward
from .serializers import (
    LGASerializer,
    LicenceTypeSerializer,
    BusinessActivitySerializer,
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


class ActivityManagePermission(permissions.BasePermission):
    """Public read for the taxonomy; OFFICER/ADMIN staff may write."""

    message = 'Only licensing officers and system admins can manage business activities.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or getattr(user, 'role', None) in {'OFFICER', 'ADMIN'})
        )


class BusinessActivityViewSet(viewsets.ModelViewSet):
    """Business activities (the "kind of business" taxonomy).

    GET /api/business-activities/?lga=<id>[&include_inactive=1]

    Public read (the applicant wizard uses it); writes are limited to
    licensing officers and admins (ActivityManagePermission).

    With ?lga= the list only includes activities that have at least one
    licence type in that council and carries the per-council licence count.
    Staff may pass ?include_inactive=1 to also see disabled activities
    (the management UI); the public list always stays active-only.
    """

    serializer_class = BusinessActivitySerializer
    permission_classes = [ActivityManagePermission]
    # The public frontend expects a plain array (contract of the old FBV).
    pagination_class = None

    def get_queryset(self):
        qs = BusinessActivity.objects.all()
        if self.action != 'list':
            # Detail routes (retrieve/update/destroy) must reach inactive
            # activities too, otherwise editing a disabled one would 404.
            return qs.order_by('order', 'name')

        user = self.request.user
        include_inactive = (
            self.request.query_params.get('include_inactive') in {'1', 'true'}
            and user.is_authenticated
            and getattr(user, 'is_lga_staff', False)
        )
        if not include_inactive:
            qs = qs.filter(is_active=True)

        lga_id = self.request.query_params.get('lga')
        if lga_id:
            qs = (
                qs.filter(licence_types__lga_id=lga_id, licence_types__category=LicenceType.Category.BUSINESS)
                .annotate(licence_type_count=Count('licence_types', filter=Q(
                    licence_types__lga_id=lga_id,
                    licence_types__category=LicenceType.Category.BUSINESS,
                )))
            )
        else:
            qs = qs.annotate(licence_type_count=Count('licence_types'))
        return qs.order_by('order', 'name')


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
    """Licence types, filterable by area, category and activity:

    GET /api/licence-types/?lga=<id>&category=BUSINESS&activity=<id>
    """

    queryset = LicenceType.objects.select_related('lga', 'activity').prefetch_related('requirements')
    serializer_class = LicenceTypeSerializer
    filterset_fields = ['lga', 'category', 'activity', 'requires_inspection']
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
