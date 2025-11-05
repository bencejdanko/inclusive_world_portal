"""
URL configuration for the portal app.
"""
from django.urls import path
from . import views
from . import fees_views

app_name = "portal"

urlpatterns = [
    # Program browsing and enrollment (members - with payment)
    path("programs/", views.program_catalog_view, name="program_catalog"),
    path("programs/<uuid:program_id>/", views.program_detail_view, name="program_detail"),
    path("programs/selection/", views.program_selection_view, name="program_selection"),
    
    # Checkout and enrollment (members)
    path("checkout/", views.checkout_view, name="checkout"),
    path("enrollment/process/", views.process_enrollment, name="process_enrollment"),
    path("enrollment/success/", views.enrollment_success_view, name="enrollment_success"),
    
    # Volunteer program enrollment (no payment required)
    path("volunteer/programs/", views.volunteer_program_catalog_view, name="volunteer_program_catalog"),
    path("volunteer/programs/selection/", views.volunteer_program_selection_view, name="volunteer_program_selection"),
    
    # Manager program management
    path("manager/programs/", views.manager_programs_view, name="manager_programs"),
    path("manager/programs/create/", views.manager_program_create_view, name="manager_program_create"),
    path("manager/programs/<uuid:program_id>/edit/", views.manager_program_edit_view, name="manager_program_edit"),
    path("manager/programs/<uuid:program_id>/people/", views.manager_program_people_view, name="manager_program_people"),
    path("manager/programs/<uuid:program_id>/add-user/", views.manager_program_add_user_view, name="manager_program_add_user"),
    path("manager/programs/<uuid:program_id>/attendance/", views.manager_program_attendance_list_view, name="manager_program_attendance"),
    path("manager/programs/<uuid:program_id>/attendance/edit/", views.manager_program_attendance_view, name="manager_program_attendance_edit"),
    path("manager/programs/<uuid:program_id>/attendance/delete/", views.manager_program_attendance_delete_view, name="manager_program_attendance_delete"),
    
    # Organization-wide people views (Manager/PCM)
    path("people/members/", views.all_members_view, name="all_members"),
    path("people/volunteers/", views.all_volunteers_view, name="all_volunteers"),
    
    # My Programs (formerly fees)
    path("my-programs/", fees_views.fees_overview_view, name="my_programs"),
    path("fees/", fees_views.fees_overview_view, name="fees"),  # Legacy redirect
    
    # My Attendance
    path("my-attendance/", views.my_attendance_view, name="my_attendance"),
]
