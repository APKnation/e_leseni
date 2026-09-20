from rest_framework import serializers

from .models import LGA, LicenceType, OfficerAssignment, Requirement


class LGASerializer(serializers.ModelSerializer):
    class Meta:
        model = LGA
        fields = ['id', 'name', 'region', 'code']


class RequirementSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)

    class Meta:
        model = Requirement
        fields = ['id', 'licence_type', 'name', 'kind', 'kind_display', 'is_mandatory', 'order']


class LicenceTypeSerializer(serializers.ModelSerializer):
    lga_name = serializers.CharField(source='lga.name', read_only=True)
    requirements = RequirementSerializer(many=True, read_only=True)

    class Meta:
        model = LicenceType
        fields = [
            'id', 'name', 'code', 'description', 'fee', 'validity_months',
            'requires_inspection', 'lga', 'lga_name', 'requirements',
        ]


class OfficerAssignmentSerializer(serializers.ModelSerializer):
    officer_name = serializers.CharField(source='officer.get_full_name', read_only=True)
    licence_type_name = serializers.CharField(source='licence_type.name', read_only=True)

    class Meta:
        model = OfficerAssignment
        fields = [
            'id', 'officer', 'officer_name', 'licence_type', 'licence_type_name',
            'can_review', 'can_inspect', 'can_approve', 'is_active', 'assigned_at',
        ]
        read_only_fields = ['assigned_at']
