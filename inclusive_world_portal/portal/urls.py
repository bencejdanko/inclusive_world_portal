"""
URL configuration for the portal app.
"""
from django.urls import path
from . import views
from . import fees_views

app_name = "portal"

urlpatterns = [
    # Program browsing and enrollment
    path("programs/", views.program_catalog_view, name="program_catalog"),
    path("programs/<uuid:program_id>/", views.program_detail_view, name="program_detail"),
    path("programs/selection/", views.program_selection_view, name="program_selection"),
    
    # Checkout and enrollment
    path("checkout/", views.checkout_view, name="checkout"),
    path("enrollment/process/", views.process_enrollment, name="process_enrollment"),
    path("enrollment/success/", views.enrollment_success_view, name="enrollment_success"),
    
    # Fees and purchases
    path("fees/", fees_views.fees_overview_view, name="fees"),
]
