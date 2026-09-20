from django.contrib import admin

from .models import Invoice, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('receipt_number', 'recorded_at')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'control_number', 'application', 'amount', 'currency', 'status', 'paid_at',
    )
    list_filter = ('status', 'currency')
    search_fields = ('control_number', 'application__reference_number', 'gepg_bill_id')
    readonly_fields = ('issued_at', 'updated_at')
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'invoice', 'amount', 'method', 'payer_name', 'paid_at')
    list_filter = ('method',)
    search_fields = ('receipt_number', 'reference', 'payer_name')
