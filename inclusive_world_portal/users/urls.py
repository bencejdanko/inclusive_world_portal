from django.urls import path

from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view
from .document_views import (
    document_editor_view, 
    export_document_pdf, 
    autogenerate_document_from_survey,
    preview_document_export,
    preview_document_export_pdf,
    download_document_export,
    delete_document_export,
    toggle_active_export,
    view_active_opd,
)
from .survey_views import (
    SurveyFormView,
)
from .dashboard_views import (
    dashboard_view,
    member_dashboard_view,
    volunteer_dashboard_view,
    pcm_dashboard_view,
    manager_dashboard_view,
)
from .notification_views import (
    notification_list_view,
    notification_detail,
    mark_notification_read,
    mark_notification_unread,
    mark_all_read,
    delete_notification,
    create_bulk_notification_view,
    notification_api_unread_count,
    notification_api_unread_list,
)
from .signup_views import RoleSelectionView
app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    
    # Role Selection for Signup
    path("role-selection/", RoleSelectionView.as_view(), name="role_selection"),
    
    # Dashboard URLs (must come before <str:username>/ pattern)
    path("dashboard/", dashboard_view, name="dashboard"),
    path("dashboard/member/", member_dashboard_view, name="member_dashboard"),
    path("dashboard/volunteer/", volunteer_dashboard_view, name="volunteer_dashboard"),
    path("dashboard/pcm/", pcm_dashboard_view, name="pcm_dashboard"),
    path("dashboard/manager/", manager_dashboard_view, name="manager_dashboard"),
    
    # Notification URLs
    path("notifications/", notification_list_view, name="notification_list"),
    path("notifications/create/", create_bulk_notification_view, name="create_notification"),
    path("notifications/<int:notification_id>/", notification_detail, name="notification_detail"),
    path("notifications/<int:notification_id>/read/", mark_notification_read, name="mark_notification_read"),
    path("notifications/<int:notification_id>/unread/", mark_notification_unread, name="mark_notification_unread"),
    path("notifications/<int:notification_id>/delete/", delete_notification, name="delete_notification"),
    path("notifications/mark-all-read/", mark_all_read, name="mark_all_read"),
    
    # Notification API endpoints
    path("api/notifications/unread-count/", notification_api_unread_count, name="api_notification_unread_count"),
    path("api/notifications/unread-list/", notification_api_unread_list, name="api_notification_unread_list"),
    
    # Document Editor
    path("documents/editor/", view=document_editor_view, name="document_editor"),
    path("documents/export-pdf/", view=export_document_pdf, name="export_document_pdf"),
    path("documents/autogenerate/", view=autogenerate_document_from_survey, name="autogenerate_document"),
    
    # Document Export Management
    path("documents/exports/<uuid:export_id>/preview/", view=preview_document_export, name="preview_document_export"),
    path("documents/exports/<uuid:export_id>/preview/pdf/", view=preview_document_export_pdf, name="preview_document_export_pdf"),
    path("documents/exports/<uuid:export_id>/download/", view=download_document_export, name="download_document_export"),
    path("documents/exports/<uuid:export_id>/delete/", view=delete_document_export, name="delete_document_export"),
    path("documents/exports/<uuid:export_id>/toggle-active/", view=toggle_active_export, name="toggle_active_export"),
    
    # View Active OPD
    path("documents/opd/", view=view_active_opd, name="view_active_opd"),
    path("documents/opd/<str:username>/", view=view_active_opd, name="view_active_opd_for_user"),
    
    # Discovery Survey URL
    path("survey/form/", SurveyFormView.as_view(), name="survey_form"),
    
    # User detail (must be last as it's a catch-all pattern)
    path("<str:username>/", view=user_detail_view, name="detail"),
]

