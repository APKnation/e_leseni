from django.db.models import Q
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response

from .models import Application, ApplicationDocument, Inspection
from .serializers import (
    ApplicationDocumentSerializer,
    ApplicationSerializer,
    ApplicationTransitionSerializer,
    InspectionSerializer,
)


class ApplicationViewSet(viewsets.ModelViewSet):
    """CRUD for licence applications.

    Applicants see their own applications; LGA staff see all applications
    for their LGA's licence types.
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
            return base
        return base.filter(applicant=user)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)

    def perform_update(self, serializer):
        # Drafts only: edits after submission go through transitions/review flows.
        instance = self.get_object()
        if instance.status not in {Application.Status.DRAFT, Application.Status.RETURNED_FOR_CORRECTION}:
            self.permission_denied(self.request)
        serializer.save()


class ApplicationTransitionView(generics.GenericAPIView):
    """POST {\"to_status\": \"SUBMITTED\", \"note\": \"...\"} to move an application."""

    serializer_class = ApplicationTransitionSerializer
    queryset = Application.objects.all()

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'application': application, 'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            application.transition_to(
                serializer.validated_data['to_status'], by=request.user, note=serializer.validated_data.get('note', '')
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ApplicationSerializer(application, context={'request': request}).data)


class ApplicationDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationDocumentSerializer
    filterset_fields = ['application', 'verified']

    def get_queryset(self):
        qs = ApplicationDocument.objects.select_related('application', 'requirement')
        user = self.request.user
        if user.is_authenticated and user.is_lga_staff:
            return qs
        return qs.filter(application__applicant=user)


class InspectionViewSet(viewsets.ModelViewSet):
    serializer_class = InspectionSerializer
    filterset_fields = ['application', 'inspector', 'passed']

    def get_queryset(self):
        qs = Inspection.objects.select_related('application', 'inspector')
        user = self.request.user
        if user.is_authenticated and user.is_lga_staff:
            return qs
        return qs.filter(application__applicant=user)
