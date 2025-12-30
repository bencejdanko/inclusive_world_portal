from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import (
    Program, Enrollment, AttendanceRecord,
    ProgramVolunteerLead, BuddyAssignment, Payment, EnrollmentSettings,
    RoleEnrollmentRequirement, Document
)
from .resources import ProgramResource, EnrollmentResource

# Basic registrations
@admin.register(Enrollment)
class EnrollmentAdmin(ImportExportModelAdmin):
    resource_class = EnrollmentResource
    list_display = ("user", "program", "status", "enrolled_at")
    list_filter = ("status", "program")
    search_fields = ("user__username", "user__name", "program__name")
    
admin.site.register(AttendanceRecord)
admin.site.register(ProgramVolunteerLead)
admin.site.register(BuddyAssignment)
admin.site.register(Payment)

# polish the admin UI 

# add filters and search
@admin.register(Program)
class ProgramAdmin(ImportExportModelAdmin):
    resource_class = ProgramResource
    list_display = ("name", "capacity", "enrolled", "archived")
    list_filter = ("archived", "enrollment_status")
    search_fields = ("name",)


@admin.register(EnrollmentSettings)
class EnrollmentSettingsAdmin(admin.ModelAdmin):
    list_display = ("enrollment_open", "closure_reason", "updated_by", "updated_at")
    readonly_fields = ("updated_at", "created_at")
    fieldsets = (
        ("Enrollment Control", {
            "fields": ("enrollment_open", "closure_reason"),
            "description": "Toggle enrollment on/off and provide a reason when closed."
        }),
        ("Metadata", {
            "fields": ("updated_by", "updated_at", "created_at"),
            "classes": ("collapse",)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance (singleton)
        return not EnrollmentSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the singleton
        return False
    
    def save_model(self, request, obj, form, change):
        # Track who made the change
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RoleEnrollmentRequirement)
class RoleEnrollmentRequirementAdmin(admin.ModelAdmin):
    list_display = ("role", "require_profile_completion", "is_active", "updated_at")
    list_filter = ("role", "is_active", "require_profile_completion")
    filter_horizontal = ("required_surveys",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Role Configuration", {
            "fields": ("role", "is_active"),
        }),
        ("Requirements", {
            "fields": ("require_profile_completion", "required_surveys"),
            "description": "Configure what users must complete before registering for programs."
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_by", "state", "published", "published_at", "source_survey", "updated_at")
    list_filter = ("state", "published", "created_at", "updated_at")
    search_fields = ("title", "user__username", "user__name", "created_by__username")
    readonly_fields = ("document_id", "created_at", "updated_at", "published_at")
    autocomplete_fields = ["user", "created_by"]
    raw_id_fields = ["source_survey"]  # Use raw_id instead of autocomplete for Survey
    fieldsets = (
        ("Document Info", {
            "fields": ("document_id", "title", "state", "published", "published_at"),
        }),
        ("Ownership", {
            "fields": ("user", "created_by", "source_survey"),
        }),
        ("Content", {
            "fields": ("content",),
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


