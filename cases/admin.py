from django.contrib import admin
from .models import Case, CaseDocument, PoliceFollowUp, CourtCase, CounselingSession

class CaseDocumentInline(admin.TabularInline):
    model = CaseDocument
    extra = 1  # Allow adding new documents inline


'''@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "status", "date_reported", "assigned_provider")
    list_filter = ("status", "date_reported")
    search_fields = ("reporter__username", "description")
    inlines = [CaseDocumentInline]
    actions = ["mark_as_under_investigation", "mark_as_resolved"]

    def mark_as_under_investigation(self, request, queryset):
        queryset.update(status="under_investigation")
    mark_as_under_investigation.short_description = "Mark selected cases as Under Investigation"

    def mark_as_resolved(self, request, queryset):
        queryset.update(status="resolved")
    mark_as_resolved.short_description = "Mark selected cases as Resolved"
'''

@admin.register(PoliceFollowUp)
class PoliceFollowUpAdmin(admin.ModelAdmin):
    list_display = ("case", "officer", "date_updated")
    search_fields = ("case__id", "officer__username")
    list_filter = ("date_updated",)


@admin.register(CourtCase)
class CourtCaseAdmin(admin.ModelAdmin):
    list_display = ("case", "court_name", "hearing_date", "verdict")
    search_fields = ("court_name", "case__id")
    list_filter = ("hearing_date",)

@admin.register(CounselingSession)
class CounselingSessionAdmin(admin.ModelAdmin):
    list_display = ("survivor", "counselor", "session_date")
    list_filter = ("session_date",)
    search_fields = ("survivor__username", "counselor__username")
    
admin.site.register(CaseDocument)

