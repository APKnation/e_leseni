from django.contrib import admin

from .models import LGA, LicenceType, BusinessActivity, OfficerAssignment, Requirement


@admin.register(BusinessActivity)
class BusinessActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'code': ('name',)}


class RequirementInline(admin.TabularInline):
    model = Requirement
    extra = 1


@admin.register(LGA)
class LGAAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'code')
    search_fields = ('name', 'region', 'code')


@admin.register(LicenceType)
class LicenceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'lga', 'category', 'activity', 'fee', 'validity_months', 'requires_inspection')
    list_filter = ('lga', 'category', 'activity', 'requires_inspection')
    search_fields = ('name', 'code')
    inlines = [RequirementInline]


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'licence_type', 'is_mandatory', 'order')
    list_filter = ('kind', 'is_mandatory')


@admin.register(OfficerAssignment)
class OfficerAssignmentAdmin(admin.ModelAdmin):
    list_display = ('officer', 'licence_type', 'can_review', 'can_inspect', 'can_approve', 'is_active')
    list_filter = ('is_active', 'can_review', 'can_inspect', 'can_approve')
