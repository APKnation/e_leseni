from django.contrib import admin

from .models import Licence, Renewal


@admin.register(Licence)
class LicenceAdmin(admin.ModelAdmin):
    list_display = (
        'licence_number', 'business_name', 'licence_type', 'lga', 'status', 'valid_until', 'issued_at',
    )
    list_filter = ('status', 'lga', 'licence_type')
    search_fields = ('licence_number', 'business_name', 'qr_token')
    readonly_fields = ('licence_number', 'qr_token', 'issued_at', 'updated_at')


@admin.register(Renewal)
class RenewalAdmin(admin.ModelAdmin):
    list_display = ('licence', 'status', 'requested_by', 'requested_at', 'decided_at')
    list_filter = ('status',)
    search_fields = ('licence__licence_number',)
