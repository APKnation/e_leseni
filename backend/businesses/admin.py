from django.contrib import admin

from .models import Business, BusinessDocument, BusinessLocation


class BusinessLocationInline(admin.TabularInline):
    model = BusinessLocation
    extra = 1


class BusinessDocumentInline(admin.TabularInline):
    model = BusinessDocument
    extra = 1


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'tin_number', 'brela_registration_number', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('name', 'tin_number', 'brela_registration_number', 'owner__username')
    inlines = [BusinessLocationInline, BusinessDocumentInline]


@admin.register(BusinessLocation)
class BusinessLocationAdmin(admin.ModelAdmin):
    list_display = ('business', 'lga', 'ward', 'street', 'is_primary')
    list_filter = ('lga', 'is_primary')


@admin.register(BusinessDocument)
class BusinessDocumentAdmin(admin.ModelAdmin):
    list_display = ('business', 'kind', 'uploaded_at')
    list_filter = ('kind',)
