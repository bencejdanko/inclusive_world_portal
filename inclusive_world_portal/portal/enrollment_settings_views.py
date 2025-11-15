"""
Views for managing enrollment settings.
Only accessible to managers.
"""
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from .models import EnrollmentSettings, RoleEnrollmentRequirement
from survey.models import Survey

logger = logging.getLogger(__name__)


@login_required
def enrollment_settings_view(request):
    """
    View and manage enrollment settings.
    Only accessible to managers.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        messages.error(request, _('Only managers can access enrollment settings.'))
        return redirect('users:dashboard')
    
    settings = EnrollmentSettings.get_settings()
    
    # Get all role requirements
    role_requirements = RoleEnrollmentRequirement.objects.all().prefetch_related('required_surveys')
    
    # Get all available surveys
    available_surveys = Survey.objects.filter(is_published=True).order_by('name')
    
    context = {
        'settings': settings,
        'role_requirements': role_requirements,
        'available_surveys': available_surveys,
    }
    
    return render(request, 'portal/enrollment_settings.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_enrollment_status(request):
    """
    Toggle enrollment open/closed status.
    Only accessible to managers.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        return JsonResponse({
            'success': False,
            'error': 'Only managers can modify enrollment settings.'
        }, status=403)
    
    try:
        settings = EnrollmentSettings.get_settings()
        
        # Toggle status
        settings.enrollment_open = not settings.enrollment_open
        settings.updated_by = request.user
        
        # Get closure reason if closing
        if not settings.enrollment_open:
            closure_reason = request.POST.get('closure_reason', '')
            settings.closure_reason = closure_reason
        
        settings.save()
        
        status = "opened" if settings.enrollment_open else "closed"
        message = f'Enrollment has been {status}.'
        
        logger.info(f"Manager {request.user.username} {status} enrollment")
        
        return JsonResponse({
            'success': True,
            'message': message,
            'enrollment_open': settings.enrollment_open,
        })
        
    except Exception as e:
        logger.error(f"Error toggling enrollment status: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def update_role_requirement(request, requirement_id):
    """
    Update enrollment requirements for a specific role.
    Only accessible to managers.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        return JsonResponse({
            'success': False,
            'error': 'Only managers can modify enrollment requirements.'
        }, status=403)
    
    try:
        requirement = get_object_or_404(RoleEnrollmentRequirement, requirement_id=requirement_id)
        
        # Update profile completion requirement
        require_profile = request.POST.get('require_profile_completion') == 'true'
        requirement.require_profile_completion = require_profile
        
        # Update active status
        is_active = request.POST.get('is_active') == 'true'
        requirement.is_active = is_active
        
        # Update required surveys
        survey_ids = request.POST.getlist('required_surveys')
        requirement.required_surveys.set(survey_ids)
        
        requirement.save()
        
        logger.info(f"Manager {request.user.username} updated requirements for {requirement.role}")
        
        return JsonResponse({
            'success': True,
            'message': f'Requirements updated for {requirement.get_role_display()}.'
        })
        
    except Exception as e:
        logger.error(f"Error updating role requirement: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def create_role_requirement(request):
    """
    Create a new role enrollment requirement.
    Only accessible to managers.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        return JsonResponse({
            'success': False,
            'error': 'Only managers can create enrollment requirements.'
        }, status=403)
    
    try:
        role = request.POST.get('role')
        
        # Check if requirement already exists for this role
        if RoleEnrollmentRequirement.objects.filter(role=role).exists():
            return JsonResponse({
                'success': False,
                'error': f'Requirements already exist for this role.'
            }, status=400)
        
        # Create new requirement
        requirement = RoleEnrollmentRequirement.objects.create(
            role=role,
            require_profile_completion=request.POST.get('require_profile_completion') == 'true',
            is_active=request.POST.get('is_active', 'true') == 'true'
        )
        
        # Add required surveys
        survey_ids = request.POST.getlist('required_surveys')
        if survey_ids:
            requirement.required_surveys.set(survey_ids)
        
        logger.info(f"Manager {request.user.username} created requirements for {role}")
        
        return JsonResponse({
            'success': True,
            'message': f'Requirements created for {requirement.get_role_display()}.',
            'requirement_id': str(requirement.requirement_id)
        })
        
    except Exception as e:
        logger.error(f"Error creating role requirement: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)
