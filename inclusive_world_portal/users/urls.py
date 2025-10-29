from django.urls import path

from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view
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

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
    
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
]
