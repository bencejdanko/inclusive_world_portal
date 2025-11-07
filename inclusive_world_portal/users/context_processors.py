from django.conf import settings


def allauth_settings(request):
    """Expose some settings from django-allauth in templates."""
    return {
        "ACCOUNT_ALLOW_REGISTRATION": settings.ACCOUNT_ALLOW_REGISTRATION,
    }


def user_alerts(request):
    """
    Provide user-specific alert data for display in top banner.
    This includes form completion status and other important notifications.
    """
    context = {}
    
    if request.user.is_authenticated:
        from inclusive_world_portal.users.models import User
        
        # Check form completion status
        profile_complete = request.user.profile_is_complete
        survey_complete = request.user.survey_is_complete
        forms_complete = request.user.forms_are_complete
        
        # Import here to avoid circular dependency
        from inclusive_world_portal.portal.models import EnrollmentSettings
        enrollment_settings = EnrollmentSettings.get_settings()
        enrollment_open = enrollment_settings.enrollment_open
        
        show_form_alert = not forms_complete
        
        context.update({
            'show_form_completion_alert': show_form_alert,
            'profile_complete': profile_complete,
            'survey_complete': survey_complete,
            'forms_complete': forms_complete,
            'enrollment_open': enrollment_open,
        })
    
    return context
