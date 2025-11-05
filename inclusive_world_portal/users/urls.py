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
    SurveyStartView,
    SurveySection1View,
    SurveySection2View,
    SurveySection3View,
    SurveySection4View,
    SurveySection5View,
    SurveySection6View,
    SurveySection7View,
    SurveySection8View,
    SurveySection9View,
    SurveySection10View,
    SurveySection11View,
    SurveySection12View,
    SurveyCompleteView,
)
from .dashboard_views import (
    dashboard_view,
    member_dashboard_view,
    volunteer_dashboard_view,
    pcm_dashboard_view,
    manager_dashboard_view,
    admin_dashboard_view,
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    
    # Dashboard URLs (must come before <str:username>/ pattern)
    path("dashboard/", dashboard_view, name="dashboard"),
    path("dashboard/member/", member_dashboard_view, name="member_dashboard"),
    path("dashboard/volunteer/", volunteer_dashboard_view, name="volunteer_dashboard"),
    path("dashboard/pcm/", pcm_dashboard_view, name="pcm_dashboard"),
    path("dashboard/manager/", manager_dashboard_view, name="manager_dashboard"),
    path("dashboard/admin/", admin_dashboard_view, name="admin_dashboard"),
    
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
    
    # Discovery Survey URLs
    path("survey/start/", SurveyStartView.as_view(), name="survey_start"),
    path("survey/1/", SurveySection1View.as_view(), name="survey_section_1"),
    path("survey/2/", SurveySection2View.as_view(), name="survey_section_2"),
    path("survey/3/", SurveySection3View.as_view(), name="survey_section_3"),
    path("survey/4/", SurveySection4View.as_view(), name="survey_section_4"),
    path("survey/5/", SurveySection5View.as_view(), name="survey_section_5"),
    path("survey/6/", SurveySection6View.as_view(), name="survey_section_6"),
    path("survey/7/", SurveySection7View.as_view(), name="survey_section_7"),
    path("survey/8/", SurveySection8View.as_view(), name="survey_section_8"),
    path("survey/9/", SurveySection9View.as_view(), name="survey_section_9"),
    path("survey/10/", SurveySection10View.as_view(), name="survey_section_10"),
    path("survey/11/", SurveySection11View.as_view(), name="survey_section_11"),
    path("survey/12/", SurveySection12View.as_view(), name="survey_section_12"),
    path("survey/complete/", SurveyCompleteView.as_view(), name="survey_complete"),
    
    # User detail (must be last as it's a catch-all pattern)
    path("<str:username>/", view=user_detail_view, name="detail"),
]
