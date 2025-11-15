from django.conf import settings


def allauth_settings(request):
    """Expose some settings from django-allauth in templates."""
    return {
        "ACCOUNT_ALLOW_REGISTRATION": settings.ACCOUNT_ALLOW_REGISTRATION,
    }


def user_alerts(request):
    """
    Provide user-specific alert data for display in top banner.
    This includes enrollment requirements status and other important notifications.
    """
    context = {}
    
    if request.user.is_authenticated:
        from inclusive_world_portal.users.models import User
        
        # Check enrollment requirements
        meets_requirements, missing_items = request.user.enrollment_requirements_status
        
        # Import here to avoid circular dependency
        from inclusive_world_portal.portal.models import EnrollmentSettings, RoleEnrollmentRequirement
        enrollment_settings = EnrollmentSettings.get_settings()
        enrollment_open = enrollment_settings.enrollment_open
        
        show_requirements_alert = not meets_requirements
        
        # Get required surveys for the user's role
        required_survey_ids = []
        try:
            requirement = RoleEnrollmentRequirement.objects.get(
                role=request.user.role,
                is_active=True
            )
            required_survey_ids = list(requirement.required_surveys.values_list('id', flat=True))
        except RoleEnrollmentRequirement.DoesNotExist:
            pass
        
        context.update({
            'show_form_completion_alert': show_requirements_alert,
            'meets_enrollment_requirements': meets_requirements,
            'missing_enrollment_items': missing_items,
            'enrollment_open': enrollment_open,
            'required_survey_ids': required_survey_ids,
        })
    
    return context
