"""
Views for Discovery Survey
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, UpdateView

from .models import DiscoverySurvey
from .survey_forms import (
    SurveySection1Form,
    SurveySection2Form,
    SurveySection3Form,
    SurveySection4Form,
    SurveySection5Form,
    SurveySection6Form,
    SurveySection7Form,
    SurveySection8Form,
    SurveySection9Form,
    SurveySection10Form,
    SurveySection11Form,
    SurveySection12Form,
)


class SurveyMixin(LoginRequiredMixin):
    """Mixin to get or create survey for current user"""
    
    def get_object(self, queryset=None):
        survey, created = DiscoverySurvey.objects.get_or_create(user=self.request.user)
        return survey


class SurveyStartView(LoginRequiredMixin, TemplateView):
    """Landing page for the discovery survey"""
    template_name = "users/survey_start.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey, created = DiscoverySurvey.objects.get_or_create(user=self.request.user)
        context['survey'] = survey
        context['profile_complete'] = self.request.user.profile_is_complete
        return context


class SurveySection1View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection1Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 1
        context['section_title'] = "About You - What Makes You Great"
        context['total_sections'] = 12
        context['next_url'] = reverse('users:survey_section_2')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_2')


class SurveySection2View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection2Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 2
        context['section_title'] = "Your Team & Important People"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_1')
        context['next_url'] = reverse('users:survey_section_3')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_3')


class SurveySection3View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection3Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 3
        context['section_title'] = "Things You Like To Do"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_2')
        context['next_url'] = reverse('users:survey_section_4')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_4')


class SurveySection4View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection4Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 4
        context['section_title'] = "Hopes, Dreams & What's Important"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_3')
        context['next_url'] = reverse('users:survey_section_5')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_5')


class SurveySection5View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection5Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 5
        context['section_title'] = "Learning & Growth"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_4')
        context['next_url'] = reverse('users:survey_section_6')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_6')


class SurveySection6View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection6Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 6
        context['section_title'] = "School & IEP Experience"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_5')
        context['next_url'] = reverse('users:survey_section_7')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_7')


class SurveySection7View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection7Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 7
        context['section_title'] = "Communication"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_6')
        context['next_url'] = reverse('users:survey_section_8')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_8')


class SurveySection8View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection8Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 8
        context['section_title'] = "Learning Preferences"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_7')
        context['next_url'] = reverse('users:survey_section_9')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_9')


class SurveySection9View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection9Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 9
        context['section_title'] = "Staff Preferences"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_8')
        context['next_url'] = reverse('users:survey_section_10')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_10')


class SurveySection10View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection10Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 10
        context['section_title'] = "Employment & Career Goals"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_9')
        context['next_url'] = reverse('users:survey_section_11')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_11')


class SurveySection11View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection11Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 11
        context['section_title'] = "Why Inclusive World & Additional Info"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_10')
        context['next_url'] = reverse('users:survey_section_12')
        return context
    
    def get_success_url(self):
        return reverse('users:survey_section_12')


class SurveySection12View(SurveyMixin, UpdateView):
    model = DiscoverySurvey
    form_class = SurveySection12Form
    template_name = "users/survey_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section_number'] = 12
        context['section_title'] = "Support Needs & Final Information"
        context['total_sections'] = 12
        context['prev_url'] = reverse('users:survey_section_11')
        context['is_last_section'] = True
        return context
    
    def form_valid(self, form):
        # Mark survey as complete
        survey = form.save(commit=False)
        survey.is_complete = True
        survey.completed_at = timezone.now()
        survey.save()
        messages.success(self.request, "Thank you! Your discovery survey is complete.")
        return redirect('users:survey_complete')


class SurveyCompleteView(LoginRequiredMixin, TemplateView):
    """Survey completion confirmation page"""
    template_name = "users/survey_complete.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['survey'] = self.request.user.discovery_survey
        except:
            pass
        context['can_purchase'] = self.request.user.can_purchase_programs
        return context
