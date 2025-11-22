"""
Views for survey list and management.
Provides robust, pre-computed survey data to avoid template logic issues.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Prefetch
from inclusive_world_portal.survey.models import Survey, Response


class SurveyItemData:
    """
    Data container for a single survey item with all computed properties.
    This eliminates complex template logic and ensures predictable rendering.
    """
    def __init__(self, survey, user):
        self.survey = survey
        self.user = user
        self._user_response = None
        self._compute_status()
    
    def _compute_status(self):
        """Pre-compute all user-specific survey status information."""
        # Get user's response if it exists
        if self.user.is_authenticated:
            try:
                # Try to use prefetched data first
                if hasattr(self.survey, 'user_responses_list'):
                    self._user_response = self.survey.user_responses_list[0] if self.survey.user_responses_list else None
                else:
                    self._user_response = self.survey.responses.filter(user=self.user).first()
            except Exception:
                self._user_response = None
        
        # Compute derived properties
        self.has_response = self._user_response is not None
        self.is_completed = self.has_response
        self.is_incomplete = not self.has_response
        
        # Action button properties
        if self.has_response:
            self.action_text = "Edit Response"
            self.action_url = self.survey.get_absolute_url()
        else:
            self.action_text = "Start"
            self.action_url = self.survey.get_absolute_url()
        
        # Status badge properties
        if self.is_completed:
            self.status_badge_class = "completed"
            self.status_badge_icon = "bi-check-circle-fill"
            self.status_badge_text = "Completed"
        else:
            self.status_badge_class = "incomplete"
            self.status_badge_icon = "bi-circle"
            self.status_badge_text = "Incomplete"
        
        # Last updated timestamp
        if self._user_response:
            self.last_updated = self._user_response.updated
        else:
            self.last_updated = None
    
    @property
    def id(self):
        return self.survey.id
    
    @property
    def name(self):
        return self.survey.name
    
    @property
    def description(self):
        return self.survey.description
    
    @property
    def expire_date(self):
        return self.survey.expire_date
    
    @property
    def need_logged_user(self):
        return self.survey.need_logged_user
    
    def to_dict(self):
        """Convert to dictionary for template context."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'expire_date': self.expire_date,
            'need_logged_user': self.need_logged_user,
            'has_response': self.has_response,
            'is_completed': self.is_completed,
            'is_incomplete': self.is_incomplete,
            'action_text': self.action_text,
            'action_url': self.action_url,
            'status_badge_class': self.status_badge_class,
            'status_badge_icon': self.status_badge_icon,
            'status_badge_text': self.status_badge_text,
            'last_updated': self.last_updated,
        }


@login_required
def survey_list_view(request):
    """
    Display list of available surveys for the current user.
    
    This view pre-computes all survey status information to avoid
    complex template logic that has caused rendering issues.
    """
    user = request.user
    
    # Get available surveys with optimized queries
    # Prefetch only the current user's responses to minimize data transfer
    user_responses_prefetch = Prefetch(
        'responses',
        queryset=Response.objects.filter(user=user).select_related('user'),
        to_attr='user_responses_list'
    )
    
    surveys_queryset = Survey.objects.filter(
        is_published=True
    ).prefetch_related(user_responses_prefetch).order_by('-expire_date', 'name')
    
    # Get required survey IDs from context processor
    from inclusive_world_portal.portal.models import RoleEnrollmentRequirement
    required_survey_ids = []
    try:
        if hasattr(user, 'role') and user.role:
            requirement = RoleEnrollmentRequirement.objects.get(
                role=user.role,
                is_active=True
            )
            required_survey_ids = list(requirement.required_surveys.values_list('id', flat=True))
    except (RoleEnrollmentRequirement.DoesNotExist, AttributeError):
        pass
    
    # Build enriched survey data
    survey_items = []
    for survey in surveys_queryset:
        # Create enriched survey item
        item_data = SurveyItemData(survey, user)
        
        # Add to list as dict for easy template access
        survey_dict = item_data.to_dict()
        survey_dict['is_required'] = survey.id in required_survey_ids
        
        survey_items.append(survey_dict)
    
    context = {
        'survey_items': survey_items,
        'required_survey_ids': required_survey_ids,
    }
    
    return render(request, 'survey/list.html', context)
