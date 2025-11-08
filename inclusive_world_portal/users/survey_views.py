"""
Views for Discovery Survey - simplified single-section version
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import UpdateView

from .models import DiscoverySurvey
from .survey_forms import DiscoverySurveyForm


class SurveyMixin(LoginRequiredMixin):
    """Mixin to get or create survey for current user"""
    
    def get_object(self, queryset=None):
        survey, created = DiscoverySurvey.objects.get_or_create(user=self.request.user)
        return survey


class SurveyFormView(SurveyMixin, UpdateView):
    """Single-page Discovery Survey Form"""
    model = DiscoverySurvey
    form_class = DiscoverySurveyForm
    template_name = "users/survey_form_single.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add flag to indicate if survey was previously completed
        context['previously_completed'] = self.object.is_complete
        return context
    
    def form_valid(self, form):
        # Mark survey as complete
        survey = form.save(commit=False)
        was_complete = survey.is_complete
        survey.is_complete = True
        if not survey.completed_at:
            survey.completed_at = timezone.now()
        survey.save()
        
        if was_complete:
            messages.success(self.request, "Your discovery questions have been updated.")
        else:
            messages.success(self.request, "Thank you! Your discovery questions are complete.")
        
        return redirect('users:dashboard')
    
    def get_success_url(self):
        return reverse('users:dashboard')
