from django.contrib import admin
from .models import (
    UserProfile, UserRole, Program, Enrollment, AttendanceRecord,
    ProgramVolunteerLead, BuddyAssignment, Notification, UserNotification,
    Survey, SurveyResponse, SurveyRoleAssociation, Payment
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
