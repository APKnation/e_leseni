from rest_framework import serializers

from .models import Licence, Renewal


class RenewalSerializer(serializers.ModelSerializer):
    licence_number = serializers.CharField(source='licence.licence_number', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)

    class Meta:
        model = Renewal
        fields = [
            'id', 'licence', 'licence_number', 'requested_by', 'requested_by_name',
            'status', 'fee_paid', 'new_valid_until', 'requested_at', 'decided_at',
        ]
        read_only_fields = ['status', 'fee_paid', 'new_valid_until', 'decided_at']


class LicenceSerializer(serializers.ModelSerializer):
    holder_name = serializers.CharField(source='holder.get_full_name', read_only=True)
    licence_type_name = serializers.CharField(source='licence_type.name', read_only=True)
    lga_name = serializers.CharField(source='lga.name', read_only=True)
    application_reference = serializers.CharField(source='application.reference_number', read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    qr_payload = serializers.SerializerMethodField()
    renewals = RenewalSerializer(many=True, read_only=True)

    class Meta:
        model = Licence
        fields = [
            'id', 'licence_number', 'application', 'application_reference',
            'business_name', 'holder', 'holder_name', 'licence_type', 'licence_type_name',
            'lga', 'lga_name', 'status', 'issued_at', 'valid_from', 'valid_until',
            'days_until_expiry', 'is_expired', 'qr_payload', 'renewals',
        ]
        read_only_fields = fields

    def get_qr_payload(self, obj):
        from .services import build_qr_payload

        return build_qr_payload(obj)


class LicenceVerifySerializer(serializers.Serializer):
    """Response shape for the public QR verification endpoint."""

    licence_number = serializers.CharField()
    business_name = serializers.CharField()
    licence_type = serializers.CharField()
    lga = serializers.CharField()
    status = serializers.CharField()
    valid_from = serializers.DateField()
    valid_until = serializers.DateField()
    is_expired = serializers.BooleanField()
