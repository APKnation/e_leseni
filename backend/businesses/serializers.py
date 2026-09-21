from rest_framework import serializers

from .models import Business, BusinessDocument, BusinessLocation


class BusinessDocumentSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)

    class Meta:
        model = BusinessDocument
        fields = ['id', 'business', 'kind', 'kind_display', 'file', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class BusinessLocationSerializer(serializers.ModelSerializer):
    lga_name = serializers.CharField(source='lga.name', read_only=True)

    class Meta:
        model = BusinessLocation
        fields = [
            'id', 'business', 'lga', 'lga_name', 'ward', 'street', 'plot_number',
            'latitude', 'longitude', 'is_primary',
        ]


class BusinessSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    locations = BusinessLocationSerializer(many=True, read_only=True)
    documents = BusinessDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'owner', 'owner_name', 'tin_number', 'brela_registration_number',
            'sector', 'is_verified', 'created_at', 'updated_at', 'locations', 'documents',
        ]
        read_only_fields = ['owner', 'is_verified', 'created_at', 'updated_at']

    def validate_name(self, value):
        # Composite DB constraint (owner, name) isn't auto-validated by DRF;
        # surface it as a 400 instead of an IntegrityError.
        owner = self.context['request'].user
        queryset = Business.objects.filter(owner=owner, name=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                'You already registered a business with this name.'
            )
        return value
