from rest_framework import serializers

from .models import Business, BusinessDocument, BusinessLocation, TINApplication


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


class TINApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TINApplication
        fields = [
            'id', 'business_name', 'taxpayer_name', 'tin_number', 'status',
            'created_at', 'processed_at',
        ]
        read_only_fields = fields


class BusinessSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_nida = serializers.CharField(source='owner.nida_number', read_only=True, default='')
    locations = BusinessLocationSerializer(many=True, read_only=True)
    documents = BusinessDocumentSerializer(many=True, read_only=True)
    has_street_id_letter = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'owner', 'owner_name', 'owner_nida', 'nida_number',
            'tin_number', 'brela_registration_number',
            'sector', 'is_verified', 'has_street_id_letter',
            'created_at', 'updated_at', 'locations', 'documents',
        ]
        read_only_fields = ['owner', 'nida_number', 'is_verified', 'created_at', 'updated_at']

    def get_has_street_id_letter(self, obj):
        return obj.documents.filter(kind=BusinessDocument.Kinds.STREET_ID_LETTER).exists()

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

    def validate_tin_number(self, value):
        """TIN is 9-12 digits when provided."""
        value = (value or '').strip()
        if value and not (value.isdigit() and 9 <= len(value) <= 12):
            raise serializers.ValidationError('TRA TIN must be 9 to 12 digits.')
        return value

    def validate_brela_registration_number(self, value):
        """BRELA registration numbers are numeric (issued by ORES/ BRELA)."""
        value = (value or '').strip()
        if value and not value.isdigit():
            raise serializers.ValidationError('BRELA registration number must contain only digits.')
        return value
