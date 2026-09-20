from rest_framework import serializers

from .models import Invoice, Payment


class PaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    invoice_control_number = serializers.CharField(source='invoice.control_number', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'invoice_control_number', 'receipt_number', 'amount',
            'method', 'method_display', 'payer_name', 'payer_phone', 'reference',
            'paid_at', 'recorded_at',
        ]
        read_only_fields = ['receipt_number', 'recorded_at']


class InvoiceSerializer(serializers.ModelSerializer):
    application_reference = serializers.CharField(source='application.reference_number', read_only=True)
    licence_type_name = serializers.CharField(source='application.licence_type.name', read_only=True)
    business_name = serializers.CharField(source='application.business.name', read_only=True)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_fully_paid = serializers.BooleanField(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'application', 'application_reference', 'licence_type_name', 'business_name',
            'control_number', 'amount', 'currency', 'status', 'gepg_bill_id', 'gepg_approval',
            'amount_paid', 'is_fully_paid', 'payments',
            'issued_at', 'control_number_expires_at', 'paid_at', 'updated_at',
        ]
        read_only_fields = fields


class InvoiceRequestControlNumberSerializer(serializers.Serializer):
    """Body for POST /invoices/{id}/control-number/ (optional; defaults apply)."""


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Payload for POST /invoices/{id}/pay/."""

    class Meta:
        model = Payment
        fields = ['amount', 'method', 'payer_name', 'payer_phone', 'reference']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Payment amount must be positive.')
        return value
