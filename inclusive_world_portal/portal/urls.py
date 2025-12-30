"""
URL configuration for the portal app.
"""
from django.urls import path
from . import views
from . import programs_views
from . import enrollment_settings_views

app_name = "portal"

urlpatterns = [
    # Program browsing and enrollment (members - with payment)
    path("catalog/", views.program_catalog_view, name="program_catalog"),
    path("catalog/<uuid:program_id>/", views.program_detail_view, name="program_detail"),
    path("catalog/selection/", views.program_selection_view, name="program_selection"),
    
    # Checkout and enrollment (members)
    path("checkout/", views.checkout_view, name="checkout"),
    path("enrollment/process/", views.process_enrollment, name="process_enrollment"),
    path("enrollment/success/", views.enrollment_success_view, name="enrollment_success"),
    
    # Volunteer program enrollment (no payment required)
    path("volunteer/catalog/", views.volunteer_program_catalog_view, name="volunteer_program_catalog"),
    path("volunteer/catalog/selection/", views.volunteer_program_selection_view, name="volunteer_program_selection"),
    
    # Program management (managers, PCMs, and program leads)
    path("program/create/", views.manager_program_create_view, name="program_create"),
    path("program/<uuid:program_id>/edit/", views.manager_program_edit_view, name="program_edit"),
    path("program/<uuid:program_id>/add-user/", views.manager_program_add_user_view, name="program_add_user"),
    path("program/<uuid:program_id>/attendance/", views.manager_program_attendance_list_view, name="program_attendance"),
    path("program/<uuid:program_id>/attendance/edit/", views.manager_program_attendance_view, name="program_attendance_edit"),
    path("program/<uuid:program_id>/attendance/delete/", views.manager_program_attendance_delete_view, name="program_attendance_delete"),
    
    # Organization-wide people views (Manager/PCM)
    path("people/members/", views.all_members_view, name="all_members"),
    path("people/volunteers/", views.all_volunteers_view, name="all_volunteers"),
    
    # Programs - unified view for all users
    path("programs/", programs_views.programs_view, name="programs"),
    
    # My Attendance
    path("my-attendance/", views.my_attendance_view, name="my_attendance"),
    
    # AJAX endpoints for enrollment management
    path("ajax/enrollment/update-status/", views.ajax_update_enrollment_status, name="ajax_update_enrollment_status"),
    path("ajax/enrollment/update-buddy/", views.ajax_update_buddy_assignment, name="ajax_update_buddy_assignment"),
    
    # Enrollment Settings (Manager only)
    path("enrollment-settings/", enrollment_settings_views.enrollment_settings_view, name="enrollment_settings"),
    path("enrollment-settings/toggle/", enrollment_settings_views.toggle_enrollment_status, name="toggle_enrollment_status"),
    path("enrollment-settings/requirement/<uuid:requirement_id>/update/", enrollment_settings_views.update_role_requirement, name="update_role_requirement"),
    path("enrollment-settings/requirement/create/", enrollment_settings_views.create_role_requirement, name="create_role_requirement"),
]
