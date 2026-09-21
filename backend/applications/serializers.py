from rest_framework import serializers

from accounts.models import User

from .permissions import allowed_statuses_for
from .models import Application, ApplicationDocument, Inspection, StatusHistory


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    requirement_name = serializers.CharField(source='requirement.name', read_only=True, default=None)

    class Meta:
        model = ApplicationDocument
        fields = ['id', 'application', 'requirement', 'requirement_name', 'file', 'uploaded_at', 'verified']
        read_only_fields = ['uploaded_at', 'verified']


class StatusHistorySerializer(serializers.ModelSerializer):
    """Audit-trail entries powering the applicant's status timeline."""

    changed_by_name = serializers.CharField(
        source='changed_by.get_full_name', read_only=True, default=''
    )

    class Meta:
        model = StatusHistory
        fields = ['from_status', 'to_status', 'changed_by_name', 'note', 'changed_at']


class ApplicationSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_is_verified = serializers.BooleanField(source='business.is_verified', read_only=True)
    licence_type_name = serializers.CharField(source='licence_type.name', read_only=True)
    lga_name = serializers.CharField(source='licence_type.lga.name', read_only=True)
    allowed_next_statuses = serializers.SerializerMethodField()
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    history = StatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'reference_number', 'applicant', 'applicant_name',
            'business', 'business_name', 'business_is_verified', 'licence_type', 'licence_type_name', 'lga_name',
            'location', 'status', 'priority', 'purpose_statement', 'rejection_reason',
            'assigned_officer', 'submitted_at', 'decided_at', 'created_at', 'updated_at',
            'allowed_next_statuses', 'documents', 'history',
        ]
        read_only_fields = [
            'applicant', 'reference_number', 'status', 'rejection_reason', 'assigned_officer',
            'submitted_at', 'decided_at', 'created_at', 'updated_at',
        ]

    def get_allowed_next_statuses(self, obj):
        """Transitions valid for the state machine AND permitted for the
        requesting user's role (drives the per-role action buttons)."""
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is not None and self.context.get('actions_by_role'):
            return sorted(s.value for s in allowed_statuses_for(user, obj))
        return sorted(s.value for s in obj.allowed_next_statuses)


class ApplicationTransitionSerializer(serializers.Serializer):
    to_status = serializers.ChoiceField(choices=Application.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_to_status(self, value):
        application = self.context['application']
        if not application.can_transition_to(value):
            allowed = sorted(s.value for s in application.allowed_next_statuses)
            raise serializers.ValidationError(
                f'Invalid transition {application.status} -> {value}. Allowed: {allowed}'
            )
        return value


class InspectionSerializer(serializers.ModelSerializer):
    inspector_name = serializers.CharField(source='inspector.get_full_name', read_only=True)
    application_reference = serializers.CharField(source='application.reference_number', read_only=True)
    # Optional on create: the view defaults the inspector to the requesting user.
    inspector = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Inspection
        fields = [
            'id', 'application', 'application_reference', 'inspector', 'inspector_name',
            'scheduled_for', 'conducted_at', 'findings', 'passed',
        ]
        read_only_fields = ['inspector_name', 'application_reference']
