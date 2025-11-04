from django.contrib import admin
from .models import (
    UserProfile, UserRole, Program, Enrollment, AttendanceRecord,
    ProgramVolunteerLead, BuddyAssignment, Notification, UserNotification,
    Survey, SurveyResponse, SurveyRoleAssociation, Payment, EnrollmentSettings
)

# Basic registrations
admin.site.register(UserRole)
admin.site.register(Enrollment)
admin.site.register(AttendanceRecord)
admin.site.register(ProgramVolunteerLead)
admin.site.register(BuddyAssignment)
admin.site.register(Notification)
admin.site.register(UserNotification)
admin.site.register(Survey)
admin.site.register(SurveyResponse)
admin.site.register(SurveyRoleAssociation)
admin.site.register(Payment)

# polish the admin UI 

# add filters and search
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "enrolled", "archived")
    list_filter = ("archived", "enrollment_status")
    search_fields = ("name",)

# link UserProfile to User in admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "status")
    search_fields = ("first_name", "last_name", "email")


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
