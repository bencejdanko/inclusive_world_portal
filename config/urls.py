from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import RedirectView
from inclusive_world_portal.payments import views as pay
from inclusive_world_portal.portal import survey_views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name='users:dashboard', permanent=False), name="home"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("inclusive_world_portal.users.urls", namespace="users")),
    # Allauth - authentication URLs
    path("accounts/", include("allauth.urls")),
    
    # Portal - Programs and Enrollment
    path("portal/", include("inclusive_world_portal.portal.urls", namespace="portal")),
    
    # Custom survey list view (overrides django-survey default)
    path("surveys/", survey_views.survey_list_view, name="survey-list"),
    
    # Django Survey - Survey creation and taking (other URLs)
    path("surveys/", include("survey.urls")),
    
    # Your stuff: custom urls includes go here
    path("pay/checkout/", pay.create_checkout, name="checkout"),
    path("stripe/webhook/", pay.stripe_webhook, name="stripe-webhook"),

    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    
    # django-hijack URLs for user impersonation
    path("hijack/", include("hijack.urls")),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]