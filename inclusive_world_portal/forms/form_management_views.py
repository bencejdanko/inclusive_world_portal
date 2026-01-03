"""
Views for survey (task) management by managers/admins.
Allows creation and editing of surveys outside the admin panel.
"""
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from .models import Form, Question
from .forms import SurveyForm, QuestionFormSet

logger = logging.getLogger(__name__)


def check_manager_permission(user):
    """Check if user has permission to manage surveys."""
    return hasattr(user, 'role') and user.role in ['manager', 'person_centered_manager']


@login_required
@require_http_methods(["GET", "POST"])
def survey_create_view(request):
    """
    Create a new survey (task).
    Only accessible to managers and person-centered managers.
    """
    if not check_manager_permission(request.user):
        messages.error(request, _('Only managers can create surveys.'))
        return redirect('survey-list')
    
    if request.method == 'POST':
        form = SurveyForm(request.POST)
        question_formset = QuestionFormSet(request.POST, prefix='questions')
        
        if form.is_valid() and question_formset.is_valid():
            # Save the survey
            survey = form.save()
            
            # Save questions
            questions = question_formset.save(commit=False)
            for question in questions:
                question.survey = survey
                question.save()
            
            messages.success(request, _('Survey "{}" created successfully.').format(survey.name))
            logger.info(f"Manager {request.user.username} created survey: {survey.name}")
            
            return redirect('forms:survey-list')
    else:
        form = SurveyForm()
        question_formset = QuestionFormSet(prefix='questions')
    
    context = {
        'form': form,
        'question_formset': question_formset,
        'is_edit': False,
    }
    
    return render(request, 'forms/form_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def survey_edit_view(request, survey_id):
    """
    Edit an existing survey (task).
    Only accessible to managers and person-centered managers.
    """
    if not check_manager_permission(request.user):
        messages.error(request, _('Only managers can edit surveys.'))
        return redirect('survey-list')
    
    survey = get_object_or_404(Form, pk=survey_id)
    
    if request.method == 'POST':
        form = SurveyForm(request.POST, instance=survey)
        question_formset = QuestionFormSet(request.POST, prefix='questions', queryset=survey.questions.all())
        
        if form.is_valid() and question_formset.is_valid():
            # Save the survey
            survey = form.save()
            
            # Save questions
            questions = question_formset.save(commit=False)
            for question in questions:
                question.survey = survey
                question.save()
            
            # Handle deleted questions
            for obj in question_formset.deleted_objects:
                obj.delete()
            
            messages.success(request, _('Survey "{}" updated successfully.').format(survey.name))
            logger.info(f"Manager {request.user.username} updated survey: {survey.name}")
            
            return redirect('forms:survey-list')
    else:
        form = SurveyForm(instance=survey)
        question_formset = QuestionFormSet(prefix='questions', queryset=survey.questions.all())
    
    context = {
        'form': form,
        'question_formset': question_formset,
        'survey': survey,
        'is_edit': True,
    }
    
    return render(request, 'forms/form_form.html', context)


@login_required
@require_http_methods(["POST"])
def survey_delete_view(request, survey_id):
    """
    Delete a survey.
    Only accessible to managers and person-centered managers.
    """
    if not check_manager_permission(request.user):
        return redirect('survey-list')
    
    survey = get_object_or_404(Form, pk=survey_id)
    survey_name = survey.name
    survey.delete()
    
    messages.success(request, _('Survey "{}" deleted successfully.').format(survey_name))
    logger.info(f"Manager {request.user.username} deleted survey: {survey_name}")
    
    return redirect('forms:survey-list')


@login_required
@require_http_methods(["POST"])
def survey_toggle_publish_view(request, survey_id):
    """
    Toggle the published status of a survey.
    Only accessible to managers and person-centered managers.
    """
    if not check_manager_permission(request.user):
        return redirect('survey-list')
    
    survey = get_object_or_404(Form, pk=survey_id)
    survey.is_published = not survey.is_published
    survey.save()
    
    status = _('published') if survey.is_published else _('unpublished')
    messages.success(request, _('Survey "{}" is now {}.').format(survey.name, status))
    logger.info(f"Manager {request.user.username} toggled publish status for survey: {survey.name} to {status}")
    
    return redirect('forms:survey-list')
