from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from applications.models import Application

from . import services
from .models import Invoice, Payment
from .serializers import (
    InvoiceRequestControlNumberSerializer,
    InvoiceSerializer,
    PaymentCreateSerializer,
    PaymentSerializer,
)


def _user_can_access_invoice(user, invoice):
    if user.is_lga_staff:
        return True
    return invoice.application.applicant_id == user.id


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """Invoices; applicants see their own, staff see all.

    Custom actions:
        POST /api/invoices/{id}/control-number/  - request a GePG control number
        POST /api/invoices/{id}/pay/             - record a payment and reconcile
    """

    serializer_class = InvoiceSerializer
    filterset_fields = ['status', 'application']
    search_fields = ['control_number', 'application__reference_number', 'application__business__name']

    def get_queryset(self):
        qs = Invoice.objects.select_related(
            'application', 'application__business', 'application__licence_type'
        ).prefetch_related('payments')
        user = self.request.user
        if user.is_lga_staff:
            return qs
        return qs.filter(application__applicant=user)

    @action(detail=True, methods=['post'], url_path='control-number')
    def control_number(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status not in {Invoice.Status.PENDING, Invoice.Status.EXPIRED}:
            return Response(
                {'detail': f'Control number already requested (status: {invoice.status}).'},
                status=status.HTTP_409_CONFLICT,
            )
        if not _user_can_access_invoice(request.user, invoice):
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        InvoiceRequestControlNumberSerializer(data=request.data).is_valid(raise_exception=True)
        updated_invoice, requested = services.request_control_number(invoice)
        if not requested:
            return Response(
                {'detail': 'GePG could not issue a control number. Try again later.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(InvoiceSerializer(updated_invoice, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        invoice = self.get_object()
        if not _user_can_access_invoice(request.user, invoice):
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        if not invoice.control_number:
            return Response(
                {'detail': 'Request a control number before paying.'}, status=status.HTTP_409_CONFLICT
            )

        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payment, settled = services.record_payment(
                invoice,
                amount=serializer.validated_data['amount'],
                method=serializer.validated_data['method'],
                payer_name=serializer.validated_data.get('payer_name', ''),
                payer_phone=serializer.validated_data.get('payer_phone', ''),
                reference=serializer.validated_data.get('reference', ''),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)

        data = PaymentSerializer(payment, context={'request': request}).data
        data['invoice_settled'] = settled
        data['application_status'] = invoice.application.status
        return Response(data, status=status.HTTP_201_CREATED)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Payment history; applicants see their own, staff see all."""

    serializer_class = PaymentSerializer
    filterset_fields = ['invoice', 'method']

    def get_queryset(self):
        qs = Payment.objects.select_related('invoice', 'invoice__application')
        user = self.request.user
        if user.is_lga_staff:
            return qs
        return qs.filter(invoice__application__applicant=user)
