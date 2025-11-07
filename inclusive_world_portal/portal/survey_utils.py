"""
Decorators and utilities for survey access control.
"""
from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import Http404

from inclusive_world_portal.portal.models import ManagedSurvey


def survey_available_for_user(view_func):
    """
    Decorator to check if a survey is available for the current user.
    Expects survey_id in the URL kwargs.
    
    Usage:
        @login_required
        @survey_available_for_user
        def take_survey(request, survey_id):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        survey_id = kwargs.get('survey_id')
        if not survey_id:
            raise Http404("Survey ID not provided")
        
        survey = get_object_or_404(ManagedSurvey, survey_id=survey_id)
        
        # Check if survey is available
        if not survey.is_available:
            status = survey.status_display
            if status == "Archived":
                messages.error(request, f"The survey '{survey.name}' has been archived and is no longer available.")
            elif status == "Inactive":
                messages.error(request, f"The survey '{survey.name}' is currently inactive.")
            elif status == "Scheduled":
                messages.info(request, f"The survey '{survey.name}' will be available starting {survey.start_date}.")
            elif status == "Expired":
                messages.warning(request, f"The survey '{survey.name}' deadline has passed ({survey.end_date}).")
            else:
                messages.error(request, f"The survey '{survey.name}' is not currently available.")
            return redirect('users:dashboard')
        
        # Check role access if user is not a manager
        if hasattr(request.user, 'role') and request.user.role != 'manager':
            user_role = request.user.role
            if not survey.is_available_for_role(user_role):
                messages.error(
                    request, 
                    f"You do not have permission to access the survey '{survey.name}'. "
                    f"This survey is restricted to specific roles."
                )
                return redirect('users:dashboard')
        
        # Add survey to request for easy access in view
        request.managed_survey = survey
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def get_available_surveys_for_user(user):
    """
    Get all surveys available to a specific user based on their role.
    
    Args:
        user: User instance
    
    Returns:
        QuerySet of ManagedSurvey objects
    """
    # Start with active, non-archived surveys
    surveys = ManagedSurvey.objects.filter(
        archived=False,
        is_active=True
    )
    
    # Managers can see all surveys
    if user.role == 'manager':
        return surveys
    
    # Filter by role
    user_role = user.role
    
    # Get surveys with no role restrictions
    surveys_for_all = surveys.filter(role_associations__isnull=True)
    
    # Get surveys specifically for user's role
    surveys_for_role = surveys.filter(role_associations__role=user_role)
    
    # Combine and remove duplicates
    available_surveys = (surveys_for_all | surveys_for_role).distinct()
    
    # Filter by date availability
    from django.utils import timezone
    now = timezone.now()
    
    available_surveys = available_surveys.exclude(
        start_date__gt=now
    ).exclude(
        end_date__lt=now
    )
    
    return available_surveys


def create_survey_completion(user, survey):
    """
    Create or get a SurveyCompletion record for a user and survey.
    
    Args:
        user: User instance
        survey: ManagedSurvey instance
    
    Returns:
        SurveyCompletion instance
    """
    from inclusive_world_portal.portal.models import SurveyCompletion, SurveyCompletionStatus
    from django.utils import timezone
    
    completion, created = SurveyCompletion.objects.get_or_create(
        user=user,
        survey=survey,
        defaults={
            'status': SurveyCompletionStatus.NOT_STARTED,
        }
    )
    
    # If just created or not started, mark as in progress
    if created or completion.status == SurveyCompletionStatus.NOT_STARTED:
        completion.status = SurveyCompletionStatus.IN_PROGRESS
        if not completion.started_at:
            completion.started_at = timezone.now()
        completion.save()
    
    return completion


def mark_survey_completed(user, survey, django_survey_response=None):
    """
    Mark a survey as completed for a user.
    
    Args:
        user: User instance
        survey: ManagedSurvey instance
        django_survey_response: Optional Response instance from django-survey
    """
    from inclusive_world_portal.portal.models import SurveyCompletion, SurveyCompletionStatus
    from django.utils import timezone
    
    completion, created = SurveyCompletion.objects.get_or_create(
        user=user,
        survey=survey,
        defaults={
            'status': SurveyCompletionStatus.COMPLETED,
            'completed_at': timezone.now(),
        }
    )
    
    if not created:
        completion.status = SurveyCompletionStatus.COMPLETED
        completion.completed_at = timezone.now()
    
    if django_survey_response:
        completion.django_survey_response = django_survey_response
    
    completion.save()
    
    return completion
