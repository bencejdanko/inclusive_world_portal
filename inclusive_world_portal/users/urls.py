from django.urls import path

from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view
from .document_views import (
    document_list_view,
    document_editor_view,
    autogenerate_document_from_survey,
    toggle_document_publish,
    view_published_document,
    serve_document_pdf,
    delete_document,
)
from .dashboard_views import (
    dashboard_view,
    member_dashboard_view,
    volunteer_dashboard_view,
    pcm_dashboard_view,
    manager_dashboard_view,
)
from .import_views import (
    user_import_view,
    process_user_import,
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
    
    # Document Management
    path("documents/", view=document_list_view, name="document_list"),
    path("documents/editor/", view=document_editor_view, name="document_editor"),
    path("documents/autogenerate/", view=autogenerate_document_from_survey, name="autogenerate_document"),
    path("documents/delete/<uuid:document_id>/", view=delete_document, name="delete_document"),
    path("documents/toggle-publish/<uuid:document_id>/", view=toggle_document_publish, name="toggle_document_publish"),
    
    # Document Viewing (requires login)
    path("documents/view/<uuid:document_id>/", view=view_published_document, name="view_published_document"),
    path("documents/pdf/<uuid:document_id>/", view=serve_document_pdf, name="serve_document_pdf"),
    
    # User Import (manager only)
    path("import/", view=user_import_view, name="user_import"),
    path("import/process/", view=process_user_import, name="process_user_import"),
        
    # User detail (must be last as it's a catch-all pattern)
    path("<str:username>/", view=user_detail_view, name="detail"),
]

