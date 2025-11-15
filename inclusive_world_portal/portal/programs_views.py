"""
Views for programs display with role-based access.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q

from .models import Enrollment, Payment, Program, EnrollmentStatus, ProgramVolunteerLead


@login_required
def programs_view(request):
    """
    Display user's programs with role-based views:
    - Regular users (member/volunteer/pcm): Shows their enrollments with status
    - Managers or Program Leads: Shows programs they manage with full details
    """
    user = request.user
    is_manager = user.role == 'manager'
    is_pcm = user.role == 'person_centered_manager'
    is_full_manager = is_manager or is_pcm
    
    # Check if user is a program lead for any programs
    user_led_program_ids = set(
        ProgramVolunteerLead.objects.filter(volunteer=user).values_list('program_id', flat=True)
    )
    has_management_access = is_full_manager or bool(user_led_program_ids)
    
    if has_management_access:
        # Management view: Show all programs user can manage
        if is_full_manager:
            # Managers and PCMs see all programs with full edit access
            programs = Program.objects.prefetch_related('volunteer_leads__volunteer').all().order_by('name')
        else:
            # Volunteer program leads see only their programs
            programs = Program.objects.filter(
                program_id__in=user_led_program_ids
            ).prefetch_related('volunteer_leads__volunteer').order_by('name')
        
        # Get user's enrollments to show their status
        user_enrollments = {
            e.program_id: e for e in Enrollment.objects.filter(user=user).select_related('program')
        }
        
        # Create a list of program data with enrollment info and edit permissions
        program_data = []
        for program in programs:
            enrollment = user_enrollments.get(program.program_id)
            # Managers and PCMs can edit all programs; volunteers can only edit programs they lead
            can_edit = is_full_manager or program.program_id in user_led_program_ids
            program_data.append({
                'program': program,
                'enrollment': enrollment,
                'status': enrollment.status if enrollment else None,
                'can_edit': can_edit,
            })
        
        # Note: users_with_active_opd removed - legacy OPD system replaced with Document model
        users_with_active_opd = set()  # Keep for template compatibility
        
        # For volunteers who are program leads, also get enrollments in programs they DON'T lead
        regular_enrollments = None
        if not is_full_manager and user_led_program_ids:
            # Get enrollments where user is NOT a lead (only for volunteer leads)
            regular_enrollments = Enrollment.objects.filter(
                user=user
            ).exclude(
                program_id__in=user_led_program_ids
            ).select_related('program').order_by('-created_at')
        
        context = {
            'has_management_access': True,
            'is_manager': is_manager,
            'is_full_manager': is_full_manager,
            'program_data': program_data,
            'programs': programs,
            'users_with_active_opd': users_with_active_opd,  # Legacy - kept for template compatibility
            'enrollment_statuses': EnrollmentStatus.choices,
            'has_programs': programs.exists(),
            'regular_enrollments': regular_enrollments,
            'has_regular_enrollments': regular_enrollments.exists() if regular_enrollments is not None else False,
        }
    else:
        # Regular user view: Show only their enrollments
        enrollments = Enrollment.objects.filter(
            user=user
        ).select_related('program').order_by('-created_at')
        
        # Get all payments for the user with related program data
        payments = Payment.objects.filter(
            user=user
        ).select_related('program').order_by('-created_at')
        
        # Calculate totals
        total_fees = sum(enrollment.program.fee for enrollment in enrollments)
        total_paid = sum(payment.amount for payment in payments if payment.status == 'succeeded')
        
        # Group enrollments by status for better organization
        approved_enrollments = enrollments.filter(status='approved')
        pending_enrollments = enrollments.filter(status='pending')
        waitlisted_enrollments = enrollments.filter(status='waitlisted')
        other_enrollments = enrollments.filter(
            Q(status='rejected') | Q(status='withdrawn')
        )
        
        context = {
            'has_management_access': False,
            'is_manager': False,
            'enrollments': enrollments,
            'approved_enrollments': approved_enrollments,
            'pending_enrollments': pending_enrollments,
            'waitlisted_enrollments': waitlisted_enrollments,
            'other_enrollments': other_enrollments,
            'payments': payments,
            'total_fees': total_fees,
            'total_paid': total_paid,
            'has_enrollments': enrollments.exists(),
            'has_payments': payments.exists(),
            'enrollment_statuses': EnrollmentStatus.choices,
        }
    
    return render(request, 'portal/programs.html', context)
