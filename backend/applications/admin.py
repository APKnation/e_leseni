from django.contrib import admin

from .models import Application, ApplicationDocument, Inspection, StatusHistory


class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 0


class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'note', 'changed_at')
    can_delete = False


class InspectionInline(admin.TabularInline):
    model = Inspection
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number', 'business', 'licence_type', 'status',
        'assigned_officer', 'priority', 'submitted_at',
    )
    list_filter = ('status', 'priority', 'licence_type__lga')
    search_fields = ('reference_number', 'business__name', 'applicant__username')
    readonly_fields = ('reference_number', 'submitted_at', 'decided_at', 'created_at', 'updated_at')
    inlines = [ApplicationDocumentInline, InspectionInline, StatusHistoryInline]


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('application', 'from_status', 'to_status', 'changed_by', 'changed_at')
    list_filter = ('to_status',)
    search_fields = ('application__reference_number',)


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('application', 'inspector', 'scheduled_for', 'conducted_at', 'passed')
    list_filter = ('passed',)
