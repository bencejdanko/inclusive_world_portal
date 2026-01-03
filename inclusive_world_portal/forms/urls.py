"""Form URLs."""
try:
    from django.conf.urls import url
except ImportError:
    # Django 4.0 replaced url with re_path
    from django.urls import re_path as url

from .views import ConfirmView, IndexView, FormCompleted, FormDetail
from .form_management_views import (
    survey_create_view,
    survey_edit_view,
    survey_delete_view,
    survey_toggle_publish_view,
)

app_name = 'forms'

urlpatterns = [
    # List view
    url(r"^$", IndexView.as_view(), name="survey-list"),
    
    # Management URLs (managers only) - MUST come before generic detail URLs
    url(r"^create/$", survey_create_view, name="survey-create"),
    url(r"^(?P<survey_id>\d+)/edit/$", survey_edit_view, name="survey-edit"),
    url(r"^(?P<survey_id>\d+)/delete/$", survey_delete_view, name="survey-delete"),
    url(r"^(?P<survey_id>\d+)/toggle-publish/$", survey_toggle_publish_view, name="survey-toggle-publish"),
    
    # Public form URLs - These should come AFTER management URLs
    url(r"^(?P<id>\d+)/completed/$", FormCompleted.as_view(), name="survey-completed"),
    url(r"^(?P<id>\d+)-(?P<step>\d+)/$", FormDetail.as_view(), name="survey-detail-step"),
    url(r"^confirm/(?P<uuid>\w+)/$", ConfirmView.as_view(), name="survey-confirmation"),
    url(r"^(?P<id>\d+)/$", FormDetail.as_view(), name="survey-detail"),  # Most generic pattern last
]
