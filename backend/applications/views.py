from django.db.models import Q
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response

from .models import Application, ApplicationDocument, Inspection
from .permissions import allowed_statuses_for
from .serializers import (
    ApplicationDocumentSerializer,
    ApplicationSerializer,
    ApplicationTransitionSerializer,
    InspectionSerializer,
)


def staff_lga_filter(user):
    """Q filter restricting objects to the user's LGA.

    ADMINs and superusers see everything; other staff only see applications
    belonging to licence types in their own LGA.
    """
    if user.is_superuser or user.role == 'ADMIN':
        return Q()
    return Q(licence_type__lga=user.lga)


def serialize_application(application, request):
    return ApplicationSerializer(application, context={'request': request}).data


class ApplicationViewSet(viewsets.ModelViewSet):
    """CRUD for licence applications.

    Applicants see their own applications; LGA staff see all applications
    for their LGA's licence types (ADMIN sees everything).
    """

    serializer_class = ApplicationSerializer
    filterset_fields = ['status', 'priority', 'licence_type', 'business']
    search_fields = ['reference_number', 'business__name', 'applicant__username']
    ordering_fields = ['created_at', 'submitted_at', 'status']

    def get_queryset(self):
        user = self.request.user
        base = Application.objects.select_related(
            'business', 'licence_type', 'licence_type__lga', 'location', 'applicant', 'assigned_officer'
        ).prefetch_related('documents')
        if user.is_authenticated and user.is_lga_staff:
            return base.filter(staff_lga_filter(user))
        return base.filter(applicant=user)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)

    def perform_update(self, serializer):
        # Drafts only: edits after submission go through transitions/review flows.
        instance = self.get_object()
        if instance.status not in {Application.Status.DRAFT, Application.Status.RETURNED_FOR_CORRECTION}:
            self.permission_denied(self.request)
        serializer.save()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # `actions_by_role` lets the serializer expose only the transitions
        # the current user may perform (drives role-specific buttons).
        context['actions_by_role'] = True
        return context


class ApplicationTransitionView(generics.GenericAPIView):
    """POST {"to_status": "SUBMITTED", "note": "..."} to move an application.

    The transition is validated against both the state machine AND the
    current user's role (see applications.permissions).
    """

    serializer_class = ApplicationTransitionSerializer
    queryset = Application.objects.all()

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        if request.user.is_authenticated and request.user.is_lga_staff and not (
            request.user.is_superuser or request.user.role == 'ADMIN'
        ):
            if not Application.objects.filter(
                pk=application.pk
            ).filter(staff_lga_filter(request.user)).exists():
                return Response(
                    {'detail': 'This application belongs to another LGA.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Role check FIRST: a forbidden transition returns 403 even when the
        # state machine would also reject it (clearer error for the client).
        to_status = request.data.get('to_status')
        allowed = allowed_statuses_for(request.user, application)
        if to_status not in allowed:
            return Response(
                {
                    'detail': f'Your role ({request.user.get_role_display() if request.user.is_authenticated else "anonymous"}) '
                    f'cannot move this application to {to_status}. Allowed: {sorted(s for s in allowed)}',
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data, context={'application': application, 'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            application.transition_to(
                to_status, by=request.user, note=serializer.validated_data.get('note', '')
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Auto-assign the acting officer when review starts.
        if to_status == Application.Status.UNDER_REVIEW and application.assigned_officer is None:
            if request.user.role == 'OFFICER':
                application.assigned_officer = request.user
                application.save(update_fields=['assigned_officer', 'updated_at'])

        return Response(serialize_application(application, request))


class ApplicationDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationDocumentSerializer
    filterset_fields = ['application', 'verified']

    def get_queryset(self):
        qs = ApplicationDocument.objects.select_related('application', 'requirement')
        user = self.request.user
        if user.is_authenticated and user.is_lga_staff:
            return qs.filter(staff_lga_filter(user))
        return qs.filter(application__applicant=user)


class InspectionViewSet(viewsets.ModelViewSet):
    serializer_class = InspectionSerializer
    filterset_fields = ['application', 'inspector', 'passed']

    def get_queryset(self):
        qs = Inspection.objects.select_related('application', 'inspector')
        user = self.request.user
        if user.is_authenticated and user.is_lga_staff:
            return qs.filter(staff_lga_filter(user))
        return qs.filter(application__applicant=user)

    def perform_create(self, serializer):
        """Schedule an inspection: OFFICER or ADMIN may assign any inspector
        (defaulting to themselves); INSPECTOR may schedule themselves."""
        user = self.request.user
        if not (user.is_superuser or user.role in {'OFFICER', 'INSPECTOR', 'ADMIN'}):
            self.permission_denied(self.request)
        inspector = serializer.validated_data.get('inspector')
        if inspector is None:
            serializer.save(inspector=user)
        else:
            serializer.save()
