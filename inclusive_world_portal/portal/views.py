"""
Views for the portal app - Program enrollment and management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
import json
import stripe

from .models import Program, Enrollment, Payment, EnrollmentSettings, EnrollmentStatus, BuddyAssignment

stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else None


@login_required
def program_catalog_view(request):
    """
    Display catalog of available programs for enrollment.
    Only accessible to users with complete profile and survey, and when enrollment is open.
    """
    enrollment_settings = EnrollmentSettings.get_settings()
    
    # Check if forms are complete
    if not request.user.forms_are_complete:
        messages.warning(
            request,
            "Please complete your profile and discovery questions before browsing programs."
        )
        return redirect('users:survey_form')
    
    # Check if enrollment is open
    if not enrollment_settings.enrollment_open:
        reason = enrollment_settings.closure_reason or "Registration is currently closed."
        messages.info(request, reason)
        return redirect('users:member_dashboard')
    
    # Get all active (non-archived) programs
    programs = Program.objects.filter(archived=False).order_by('name')
    
    # Get user's existing enrollments to mark already enrolled programs
    enrolled_program_ids = request.user.enrollments.values_list('program_id', flat=True)
    
    context = {
        'programs': programs,
        'enrolled_program_ids': list(enrolled_program_ids),
        'enrollment_settings': enrollment_settings,
    }
    
    return render(request, 'portal/program_catalog.html', context)


@login_required
def program_detail_view(request, program_id):
    """
    Display detailed information about a specific program.
    Can be used for the info icon modal/page.
    """
    program = get_object_or_404(Program, program_id=program_id)
    
    # Check if user is already enrolled
    is_enrolled = request.user.enrollments.filter(program=program).exists()
    
    context = {
        'program': program,
        'is_enrolled': is_enrolled,
    }
    
    # Return JSON for AJAX requests (modal use case)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'program_id': str(program.program_id),
            'name': program.name,
            'description': program.description,
            'fee': str(program.fee),
            'capacity': program.capacity,
            'enrolled': program.enrolled,
            'available_spots': program.available_spots,
            'start_date': program.start_date.isoformat() if program.start_date else None,
            'end_date': program.end_date.isoformat() if program.end_date else None,
            'image_url': program.image.url if program.image else None,
            'is_enrolled': is_enrolled,
        })
    
    return render(request, 'portal/program_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def program_selection_view(request):
    """
    Handle program selection and ranking.
    GET: Display selection interface with selected programs from URL
    POST: Process ranked selections and proceed to checkout
    """
    enrollment_settings = EnrollmentSettings.get_settings()
    
    # Check forms completion
    if not request.user.forms_are_complete:
        messages.warning(
            request,
            "Please complete your profile and discovery questions before enrolling in programs."
        )
        return redirect('users:survey_form')
    
    # Check if enrollment is open
    if not enrollment_settings.enrollment_open:
        reason = enrollment_settings.closure_reason or "Registration is currently closed."
        messages.info(request, reason)
        return redirect('users:member_dashboard')
    
    if request.method == 'POST':
        # Get selected program IDs and their rankings from POST data
        try:
            selections_data = json.loads(request.POST.get('selections', '[]'))
            
            if not selections_data:
                messages.error(request, "Please select at least one program.")
                return redirect('portal:program_catalog')
            
            # Validate all programs exist and are available
            program_ids = [item['program_id'] for item in selections_data]
            programs = Program.objects.filter(
                program_id__in=program_ids,
                archived=False
            )
            
            if len(programs) != len(program_ids):
                messages.error(request, "Some selected programs are no longer available.")
                return redirect('portal:program_catalog')
            
            # Store selections in session for checkout
            request.session['program_selections'] = selections_data
            
            return redirect('portal:checkout')
            
        except (json.JSONDecodeError, KeyError) as e:
            messages.error(request, "Invalid selection data. Please try again.")
            return redirect('portal:program_catalog')
    
    # GET request - get program IDs from URL parameter
    programs_param = request.GET.get('programs', '')
    
    if not programs_param:
        messages.warning(request, "No programs selected. Please select programs first.")
        return redirect('portal:program_catalog')
    
    # Parse program IDs from comma-separated string
    program_ids = [pid.strip() for pid in programs_param.split(',') if pid.strip()]
    
    if not program_ids:
        messages.warning(request, "No programs selected. Please select programs first.")
        return redirect('portal:program_catalog')
    
    # Get program objects (maintain order from URL)
    selected_programs = []
    for program_id in program_ids:
        try:
            program = Program.objects.get(program_id=program_id, archived=False)
            selected_programs.append(program)
        except Program.DoesNotExist:
            continue
    
    if not selected_programs:
        messages.error(request, "Selected programs are not available.")
        return redirect('portal:program_catalog')
    
    context = {
        'selected_programs': selected_programs,
    }
    
    return render(request, 'portal/program_selection.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def checkout_view(request):
    """
    Display checkout page with program selections and Stripe payment.
    """
    enrollment_settings = EnrollmentSettings.get_settings()
    
    # Check forms completion
    if not request.user.forms_are_complete:
        messages.warning(request, "Please complete your profile and discovery questions first.")
        return redirect('users:survey_form')
    
    # Check if enrollment is open
    if not enrollment_settings.enrollment_open:
        reason = enrollment_settings.closure_reason or "Registration is currently closed."
        messages.info(request, reason)
        return redirect('users:member_dashboard')
    
    # Get selections from session
    selections_data = request.session.get('program_selections', [])
    
    if not selections_data:
        messages.warning(request, "No programs selected. Please select programs first.")
        return redirect('portal:program_catalog')
    
    # Get program details
    program_ids = [item['program_id'] for item in selections_data]
    programs = Program.objects.filter(program_id__in=program_ids, archived=False)
    
    # Create a mapping of program_id to rank
    rank_map = {item['program_id']: item['rank'] for item in selections_data}
    
    # Add rank to each program and sort
    programs_with_rank = []
    for program in programs:
        program.rank = rank_map.get(str(program.program_id), 999)
        programs_with_rank.append(program)
    
    programs_with_rank.sort(key=lambda p: p.rank)
    
    # Calculate total
    total_amount = sum(program.fee for program in programs_with_rank)
    
    # Create Stripe Payment Intent if Stripe is configured
    stripe_client_secret = None
    stripe_public_key = getattr(settings, 'STRIPE_PUBLIC_KEY', None)
    
    if stripe.api_key and request.method == 'GET':
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total_amount * 100),  # Convert to cents
                currency='usd',
                metadata={
                    'user_id': str(request.user.id),
                    'program_ids': ','.join(program_ids),
                }
            )
            stripe_client_secret = intent.client_secret
        except Exception as e:
            messages.error(request, f"Payment system error: {str(e)}")
    
    context = {
        'programs': programs_with_rank,
        'total_amount': total_amount,
        'stripe_public_key': stripe_public_key,
        'stripe_client_secret': stripe_client_secret,
    }
    
    return render(request, 'portal/checkout.html', context)


@login_required
@require_http_methods(["POST"])
def process_enrollment(request):
    """
    Process successful payment and create enrollments.
    Called after Stripe payment succeeds.
    """
    try:
        # Get payment intent ID from Stripe
        payment_intent_id = request.POST.get('payment_intent_id')
        
        if not payment_intent_id:
            return JsonResponse({'error': 'Missing payment intent'}, status=400)
        
        # Retrieve payment intent from Stripe
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        except Exception as e:
            return JsonResponse({'error': f'Invalid payment: {str(e)}'}, status=400)
        
        if intent.status != 'succeeded':
            return JsonResponse({'error': 'Payment not completed'}, status=400)
        
        # Get selections from session
        selections_data = request.session.get('program_selections', [])
        
        if not selections_data:
            return JsonResponse({'error': 'No selections found'}, status=400)
        
        # Create enrollments for each program with rank
        enrollments_created = []
        
        for selection in selections_data:
            program = get_object_or_404(
                Program,
                program_id=selection['program_id'],
                archived=False
            )
            
            # Create or update enrollment
            enrollment, created = Enrollment.objects.update_or_create(
                user=request.user,
                program=program,
                defaults={
                    'status': 'pending',  # Will be reviewed by staff
                    'preference_order': selection['rank'],
                }
            )
            enrollments_created.append(enrollment)
        
        # Clear session
        request.session.pop('program_selections', None)
        request.session.pop('selected_program_ids', None)
        
        messages.success(
            request,
            f"Successfully enrolled in {len(enrollments_created)} program(s)! "
            "Your enrollment will be reviewed by our team."
        )
        
        return JsonResponse({
            'success': True,
            'redirect_url': request.build_absolute_uri('/users/dashboard/member/')
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def enrollment_success_view(request):
    """
    Display success page after enrollment.
    """
    context = {}
    return render(request, 'portal/enrollment_success.html', context)


# -------------------------
# Volunteer-specific views (no payment required)
# -------------------------

@login_required
def volunteer_program_catalog_view(request):
    """
    Display catalog of available programs for volunteer enrollment.
    Same as regular catalog but for volunteers (no payment required).
    Only accessible to volunteers, managers, and person-centered managers with complete profile and survey, and when enrollment is open.
    """
    # Check if user is a volunteer, manager, or person-centered manager
    if request.user.role not in ['volunteer', 'manager', 'person_centered_manager']:
        messages.error(request, "This page is only accessible to volunteers, managers, and person-centered managers.")
        return redirect('home')
    
    enrollment_settings = EnrollmentSettings.get_settings()
    
    # Check if forms are complete
    if not request.user.forms_are_complete:
        messages.warning(
            request,
            "Please complete your profile and discovery questions before browsing programs."
        )
        return redirect('users:survey_form')
    
    # Check if enrollment is open
    if not enrollment_settings.enrollment_open:
        reason = enrollment_settings.closure_reason or "Registration is currently closed."
        messages.info(request, reason)
        # Redirect to appropriate dashboard based on role
        if request.user.role == 'manager':
            return redirect('users:manager_dashboard')
        elif request.user.role == 'person_centered_manager':
            return redirect('users:pcm_dashboard')
        else:
            return redirect('users:volunteer_dashboard')
    
    # Get all active (non-archived) programs
    programs = Program.objects.filter(archived=False).order_by('name')
    
    # Get user's existing enrollments to mark already enrolled programs
    enrolled_program_ids = request.user.enrollments.values_list('program_id', flat=True)
    
    context = {
        'programs': programs,
        'enrolled_program_ids': list(enrolled_program_ids),
        'enrollment_settings': enrollment_settings,
        'is_volunteer': True,
    }
    
    return render(request, 'portal/volunteer_program_catalog.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def volunteer_program_selection_view(request):
    """
    Handle volunteer program selection and ranking.
    Same as regular selection but without payment processing.
    GET: Display selection interface with selected programs from URL
    POST: Process ranked selections and directly create enrollments
    """
    # Check if user is a volunteer, manager, or person-centered manager
    if request.user.role not in ['volunteer', 'manager', 'person_centered_manager']:
        messages.error(request, "This page is only accessible to volunteers, managers, and person-centered managers.")
        return redirect('home')
    
    enrollment_settings = EnrollmentSettings.get_settings()
    
    # Check forms completion
    if not request.user.forms_are_complete:
        messages.warning(
            request,
            "Please complete your profile and discovery questions before enrolling in programs."
        )
        return redirect('users:survey_form')
    
    # Check if enrollment is open
    if not enrollment_settings.enrollment_open:
        reason = enrollment_settings.closure_reason or "Registration is currently closed."
        messages.info(request, reason)
        # Redirect to appropriate dashboard based on role
        if request.user.role == 'manager':
            return redirect('users:manager_dashboard')
        elif request.user.role == 'person_centered_manager':
            return redirect('users:pcm_dashboard')
        else:
            return redirect('users:volunteer_dashboard')
    
    if request.method == 'POST':
        # Get selected program IDs and their rankings from POST data
        try:
            selections_data = json.loads(request.POST.get('selections', '[]'))
            
            if not selections_data:
                messages.error(request, "Please select at least one program.")
                return redirect('portal:volunteer_program_catalog')
            
            # Validate all programs exist and are available
            program_ids = [item['program_id'] for item in selections_data]
            programs = Program.objects.filter(
                program_id__in=program_ids,
                archived=False
            )
            
            if len(programs) != len(program_ids):
                messages.error(request, "Some selected programs are no longer available.")
                return redirect('portal:volunteer_program_catalog')
            
            # Create enrollments directly (no payment needed for volunteers)
            enrollments_created = []
            
            for selection in selections_data:
                program = get_object_or_404(
                    Program,
                    program_id=selection['program_id'],
                    archived=False
                )
                
                # Create or update enrollment
                enrollment, created = Enrollment.objects.update_or_create(
                    user=request.user,
                    program=program,
                    defaults={
                        'status': 'pending',  # Will be reviewed by staff
                        'preference_order': selection['rank'],
                    }
                )
                enrollments_created.append(enrollment)
            
            messages.success(
                request,
                f"Successfully enrolled in {len(enrollments_created)} program(s)! "
                "Your enrollment will be reviewed by our team."
            )
            
            # Redirect to appropriate dashboard based on role
            if request.user.role == 'manager':
                return redirect('users:manager_dashboard')
            elif request.user.role == 'person_centered_manager':
                return redirect('users:pcm_dashboard')
            else:
                return redirect('users:volunteer_dashboard')
            
        except (json.JSONDecodeError, KeyError) as e:
            messages.error(request, "Invalid selection data. Please try again.")
            return redirect('portal:volunteer_program_catalog')
    
    # GET request - get program IDs from URL parameter
    programs_param = request.GET.get('programs', '')
    
    if not programs_param:
        messages.warning(request, "No programs selected. Please select programs first.")
        return redirect('portal:volunteer_program_catalog')
    
    # Parse program IDs from comma-separated string
    program_ids = [pid.strip() for pid in programs_param.split(',') if pid.strip()]
    
    if not program_ids:
        messages.warning(request, "No programs selected. Please select programs first.")
        return redirect('portal:volunteer_program_catalog')
    
    # Get program objects (maintain order from URL)
    selected_programs = []
    for program_id in program_ids:
        try:
            program = Program.objects.get(program_id=program_id, archived=False)
            selected_programs.append(program)
        except Program.DoesNotExist:
            continue
    
    if not selected_programs:
        messages.error(request, "Selected programs are not available.")
        return redirect('portal:volunteer_program_catalog')
    
    context = {
        'selected_programs': selected_programs,
        'is_volunteer': True,
    }
    
    return render(request, 'portal/volunteer_program_selection.html', context)


# -------------------------
# Manager Program Management Views
# -------------------------

@login_required
def manager_programs_view(request):
    """
    Display all programs (including archived) for manager to manage.
    Only accessible to managers.
    Styled like the catalog view but with edit buttons instead of select buttons.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        messages.error(request, "This page is only accessible to managers.")
        return redirect('home')
    
    # Get all programs (including archived), ordered by name
    # Prefetch volunteer leads for efficient display
    programs = Program.objects.prefetch_related('volunteer_leads__volunteer').all().order_by('name')
    
    # Get users with active OPDs for all volunteer leads
    from inclusive_world_portal.portal.models import ProgramVolunteerLead, DocumentExport
    lead_user_ids = ProgramVolunteerLead.objects.values_list('volunteer_id', flat=True).distinct()
    active_exports = DocumentExport.objects.filter(
        is_active=True,
        user_id__in=lead_user_ids
    ).values_list('user_id', flat=True)
    users_with_active_opd = set(active_exports)
    
    context = {
        'programs': programs,
        'users_with_active_opd': users_with_active_opd,
    }
    
    return render(request, 'portal/manager_programs_list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def manager_program_create_view(request):
    """
    Create a new program.
    Only accessible to managers.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        messages.error(request, "This page is only accessible to managers.")
        return redirect('home')
    
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        fee = request.POST.get('fee', '0')
        capacity = request.POST.get('capacity', '').strip()
        image = request.FILES.get('image')  # Get uploaded image file
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        enrollment_status = request.POST.get('enrollment_status', '').strip()
        archived = request.POST.get('archived') == 'on'
        
        # Basic validation
        if not name:
            messages.error(request, "Program name is required.")
            return render(request, 'portal/manager_program_form.html', {
                'form_data': request.POST,
                'is_create': True,
            })
        
        try:
            # Create the program
            program = Program.objects.create(
                name=name,
                description=description,
                fee=fee if fee else '0.00',
                capacity=int(capacity) if capacity else None,
                image=image,  # Save uploaded image
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None,
                enrollment_status=enrollment_status,
                archived=archived,
            )
            
            messages.success(request, f"Program '{program.name}' created successfully!")
            return redirect('portal:manager_programs')
            
        except Exception as e:
            messages.error(request, f"Error creating program: {str(e)}")
            return render(request, 'portal/manager_program_form.html', {
                'form_data': request.POST,
                'is_create': True,
            })
    
    # GET request
    context = {
        'is_create': True,
    }
    
    return render(request, 'portal/manager_program_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def manager_program_edit_view(request, program_id):
    """
    Edit an existing program.
    Only accessible to managers.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        messages.error(request, "This page is only accessible to managers.")
        return redirect('home')
    
    program = get_object_or_404(Program, program_id=program_id)
    
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        fee = request.POST.get('fee', '0')
        capacity = request.POST.get('capacity', '').strip()
        image = request.FILES.get('image')  # Get uploaded image file
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        enrollment_status = request.POST.get('enrollment_status', '').strip()
        archived = request.POST.get('archived') == 'on'
        
        # Basic validation
        if not name:
            messages.error(request, "Program name is required.")
            return render(request, 'portal/manager_program_form.html', {
                'program': program,
                'is_create': False,
            })
        
        try:
            # Update the program
            program.name = name
            program.description = description
            program.fee = fee if fee else '0.00'
            program.capacity = int(capacity) if capacity else None
            # Only update image if a new one was uploaded
            if image:
                program.image = image
            program.start_date = start_date if start_date else None
            program.end_date = end_date if end_date else None
            program.enrollment_status = enrollment_status
            program.archived = archived
            program.save()
            
            messages.success(request, f"Program '{program.name}' updated successfully!")
            return redirect('portal:manager_programs')
            
        except Exception as e:
            messages.error(request, f"Error updating program: {str(e)}")
            return render(request, 'portal/manager_program_form.html', {
                'program': program,
                'is_create': False,
            })
    
    # GET request
    context = {
        'program': program,
        'is_create': False,
    }
    
    return render(request, 'portal/manager_program_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])


@login_required
@require_http_methods(["GET", "POST"])
def manager_program_add_user_view(request, program_id):
    """
    Search and add users (members or volunteers) to a program.
    Only accessible to managers.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        messages.error(request, "This page is only accessible to managers.")
        return redirect('home')
    
    program = get_object_or_404(Program, program_id=program_id)
    
    # Get the 'next' parameter to determine where to redirect back
    next_page = request.GET.get('next', 'all_members')
    
    if request.method == 'POST':
        # Add user to program
        user_id = request.POST.get('user_id')
        next_page = request.POST.get('next', 'all_members')
        
        try:
            from inclusive_world_portal.users.models import User
            from .models import Enrollment, EnrollmentStatus
            
            user = get_object_or_404(User, id=user_id)
            
            # Check if already enrolled
            existing = Enrollment.objects.filter(program=program, user=user).first()
            if existing:
                messages.warning(request, f"{user.name} is already enrolled in this program.")
            else:
                # Create enrollment with pending status
                Enrollment.objects.create(
                    program=program,
                    user=user,
                    status=EnrollmentStatus.PENDING,
                    assigned_by=request.user,
                    assigned_at=timezone.now()
                )
                messages.success(request, f"Successfully added {user.name} to the program with pending status.")
            
            from django.urls import reverse
            # Redirect to the appropriate page based on next parameter
            if next_page == 'all_volunteers':
                return redirect(reverse('portal:all_volunteers') + f'?course={program_id}')
            else:
                return redirect(reverse('portal:all_members') + f'?course={program_id}')
        except Exception as e:
            messages.error(request, f"Error adding user: {str(e)}")
            return redirect('portal:manager_program_add_user', program_id=program_id)
    
    # GET request - search users
    query = request.GET.get('q', '').strip()
    users = []
    enrolled_user_ids = []
    
    if query:
        from inclusive_world_portal.users.models import User
        from django.db.models import Q
        
        # Search for users by name, username, or email
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(name__icontains=query)
        ).order_by('name', 'username')[:20]
        
        # Get list of already enrolled user IDs
        from .models import Enrollment
        enrolled_user_ids = list(
            Enrollment.objects.filter(program=program)
            .values_list('user_id', flat=True)
        )
    
    context = {
        'program': program,
        'query': query,
        'users': users,
        'enrolled_user_ids': enrolled_user_ids,
        'next_page': next_page,
    }
    
    return render(request, 'portal/manager_program_add_user.html', context)


@login_required
@require_http_methods(["GET"])
def manager_program_attendance_list_view(request, program_id):
    """
    List all attendance records for a program.
    Display attendance records grouped by date with edit and add options.
    Only accessible to managers.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        messages.error(request, "This page is only accessible to managers.")
        return redirect('home')
    
    program = get_object_or_404(Program, program_id=program_id)
    
    from .models import AttendanceRecord
    from datetime import date
    from django.db.models import Count
    
    # Get all unique attendance dates for this program, ordered by date descending
    attendance_dates = AttendanceRecord.objects.filter(
        program=program
    ).values('attendance_date').annotate(
        participant_count=Count('user', distinct=True)
    ).order_by('-attendance_date')
    
    context = {
        'program': program,
        'attendance_dates': attendance_dates,
    }
    
    return render(request, 'portal/manager_program_attendance_list.html', context)


@login_required
@require_http_methods(["POST"])
def manager_program_attendance_delete_view(request, program_id):
    """
    Delete all attendance records for a specific program and date.
    Only accessible to managers.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        messages.error(request, "This page is only accessible to managers.")
        return redirect('home')
    
    program = get_object_or_404(Program, program_id=program_id)
    
    from .models import AttendanceRecord
    from datetime import datetime
    
    # Get the date from POST data
    attendance_date_str = request.POST.get('date')
    if not attendance_date_str:
        messages.error(request, "No date specified.")
        return redirect('portal:manager_program_attendance', program_id=program_id)
    
    try:
        attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
        
        # Delete all attendance records for this program and date
        deleted_count, _ = AttendanceRecord.objects.filter(
            program=program,
            attendance_date=attendance_date
        ).delete()
        
        if deleted_count > 0:
            messages.success(request, f"Deleted attendance records for {attendance_date.strftime('%B %d, %Y')} ({deleted_count} record{'s' if deleted_count != 1 else ''}).")
        else:
            messages.info(request, f"No attendance records found for {attendance_date.strftime('%B %d, %Y')}.")
            
    except ValueError:
        messages.error(request, "Invalid date format.")
    except Exception as e:
        messages.error(request, f"Error deleting attendance: {str(e)}")
    
    return redirect('portal:manager_program_attendance', program_id=program_id)


@login_required
@require_http_methods(["GET", "POST"])
def manager_program_attendance_view(request, program_id):
    """
    Add or edit attendance for a program on a specific date.
    - Display attendance date selector
    - Show all approved members and volunteers
    - Allow marking attendance status (Present, Tardy, Informed, Uninformed)
    - Allow entering hours for volunteers
    - Allow adding notes
    Only accessible to managers.
    """
    # Check if user is a manager
    if request.user.role != 'manager':
        messages.error(request, "This page is only accessible to managers.")
        return redirect('home')
    
    program = get_object_or_404(Program, program_id=program_id)
    
    from .models import Enrollment, EnrollmentStatus, AttendanceRecord, AttendanceStatus
    from inclusive_world_portal.users.models import User
    from datetime import date
    
    # Get attendance date from query parameter or default to today
    attendance_date_str = request.GET.get('date', '')
    if attendance_date_str:
        try:
            from datetime import datetime
            attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
        except ValueError:
            attendance_date = date.today()
    else:
        attendance_date = date.today()
    
    if request.method == 'POST':
        # Process attendance submissions
        try:
            # Get the date from POST data
            attendance_date_str = request.POST.get('attendance_date')
            if attendance_date_str:
                from datetime import datetime
                attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
            
            # Process each user's attendance
            for key, value in request.POST.items():
                if key.startswith('attendance_status_'):
                    user_id = key.replace('attendance_status_', '')
                    attendance_status_value = value
                    
                    # Get hours and notes for this user
                    hours_str = request.POST.get(f'hours_{user_id}', '').strip()
                    notes = request.POST.get(f'notes_{user_id}', '').strip()
                    
                    # Parse hours (only for volunteers)
                    hours = None
                    if hours_str:
                        try:
                            hours = float(hours_str)
                        except ValueError:
                            pass
                    
                    # Get the user
                    try:
                        user = User.objects.get(id=user_id)
                    except User.DoesNotExist:
                        continue
                    
                    # Create or update attendance record
                    AttendanceRecord.objects.update_or_create(
                        program=program,
                        user=user,
                        attendance_date=attendance_date,
                        defaults={
                            'attendance_status': attendance_status_value,
                            'hours': hours,
                            'notes': notes,
                        }
                    )
            
            messages.success(request, f"Attendance saved for {attendance_date.strftime('%B %d, %Y')}.")
            return redirect('portal:manager_program_attendance', program_id=program_id)
            
        except Exception as e:
            messages.error(request, f"Error saving attendance: {str(e)}")
            return redirect(request.path)
    
    # GET request - gather all data
    # Get all approved enrollments for this program
    approved_enrollments = Enrollment.objects.filter(
        program=program,
        status=EnrollmentStatus.APPROVED
    ).select_related('user').order_by('user__name')
    
    # Get existing attendance records for this date
    existing_attendance = AttendanceRecord.objects.filter(
        program=program,
        attendance_date=attendance_date
    ).select_related('user')
    
    # Create a map of user_id -> attendance_record
    attendance_map = {ar.user_id: ar for ar in existing_attendance}
    
    # Prepare participants list with attendance data
    participants = []
    for enrollment in approved_enrollments:
        user = enrollment.user
        attendance_record = attendance_map.get(user.id)
        
        # Determine if user is a volunteer (includes managers and person-centered managers)
        is_volunteer = user.role in ['volunteer', 'manager', 'person_centered_manager']
        
        # Default values: 'present' for attendance, 1.5 hours for volunteers
        default_attendance_status = 'present'
        default_hours = 1.5 if is_volunteer else None
        
        participants.append({
            'user': user,
            'role': user.get_role_display() if hasattr(user, 'get_role_display') else user.role.title(),
            'is_volunteer': is_volunteer,
            'attendance_status': attendance_record.attendance_status if attendance_record else default_attendance_status,
            'hours': attendance_record.hours if attendance_record else default_hours,
            'notes': attendance_record.notes if attendance_record else '',
        })
    
    context = {
        'program': program,
        'attendance_date': attendance_date,
        'participants': participants,
        'attendance_statuses': AttendanceStatus.choices,
    }
    
    return render(request, 'portal/manager_program_attendance.html', context)


@login_required
def my_attendance_view(request):
    """
    Display user's attendance records across all programs.
    Shows total hours for volunteers.
    """
    from decimal import Decimal
    from .models import AttendanceRecord
    
    # Get all attendance records for the user, ordered by date (most recent first)
    attendance_records = AttendanceRecord.objects.filter(
        user=request.user
    ).select_related('program').order_by('-attendance_date')
    
    # Calculate total hours if user is a volunteer (includes managers and person-centered managers)
    total_hours = Decimal('0.00')
    is_volunteer = request.user.role in ['volunteer', 'manager', 'person_centered_manager']
    
    if is_volunteer:
        for record in attendance_records:
            if record.hours:
                total_hours += record.hours
    
    context = {
        'attendance_records': attendance_records,
        'total_hours': total_hours,
        'is_volunteer': is_volunteer,
    }
    
    return render(request, 'portal/my_attendance.html', context)


# -------------------------
# Organization-wide People Views (Manager/PCM)
# -------------------------

@login_required
def all_members_view(request):
    """
    Display all members across all programs.
    Shows Name (with profile link), Status (changeable dropdown), and Role (read-only).
    Accessible to managers and person-centered managers.
    Note: Member roles cannot be changed from this view.
    """
    # Check if user is a manager or person-centered manager
    if request.user.role not in ['manager', 'person_centered_manager']:
        messages.error(request, "This page is only accessible to managers and person-centered managers.")
        return redirect('home')
    
    from inclusive_world_portal.users.models import User
    from django.db.models import Q
    
    # Handle POST requests for status updates (managers only)
    if request.method == 'POST' and request.user.role == 'manager':
        action = request.POST.get('action')
        
        if action == 'update_status':
            user_id = request.POST.get('user_id')
            new_status = request.POST.get('status')
            
            try:
                member = get_object_or_404(User, id=user_id)
                
                # Validate status
                valid_statuses = [choice[0] for choice in User.Status.choices]
                if new_status in valid_statuses:
                    member.status = new_status
                    member.save()
                    messages.success(request, f"Status updated for {member.name or member.username}.")
                else:
                    messages.error(request, "Invalid status selection.")
            except Exception as e:
                messages.error(request, f"Error updating status: {str(e)}")
            
            # Preserve course filter when redirecting
            course_filter = request.POST.get('course_filter', '')
            redirect_url = 'portal:all_members'
            if course_filter:
                from django.urls import reverse
                redirect_url = reverse('portal:all_members') + f'?course={course_filter}'
                return redirect(redirect_url)
            return redirect('portal:all_members')
        
        elif action == 'update_enrollment_status':
            enrollment_id = request.POST.get('enrollment_id')
            new_status = request.POST.get('enrollment_status')
            
            try:
                enrollment = get_object_or_404(Enrollment, enrollment_id=enrollment_id)
                
                # Validate status
                valid_statuses = [choice[0] for choice in EnrollmentStatus.choices]
                if new_status in valid_statuses:
                    old_status = enrollment.status
                    enrollment.status = new_status
                    enrollment.assigned_by = request.user
                    enrollment.assigned_at = timezone.now()
                    enrollment.save()
                    
                    # Update program enrolled count if status changed to/from approved
                    program = enrollment.program
                    if old_status != EnrollmentStatus.APPROVED and new_status == EnrollmentStatus.APPROVED:
                        program.enrolled += 1
                        program.save()
                    elif old_status == EnrollmentStatus.APPROVED and new_status != EnrollmentStatus.APPROVED:
                        program.enrolled = max(0, program.enrolled - 1)
                        program.save()
                    
                    messages.success(request, f"Enrollment status updated for {enrollment.user.name or enrollment.user.username}.")
                else:
                    messages.error(request, "Invalid enrollment status selection.")
            except Exception as e:
                messages.error(request, f"Error updating enrollment status: {str(e)}")
            
            # Preserve course filter when redirecting
            course_filter = request.POST.get('course_filter', '')
            redirect_url = 'portal:all_members'
            if course_filter:
                from django.urls import reverse
                redirect_url = reverse('portal:all_members') + f'?course={course_filter}'
                return redirect(redirect_url)
            return redirect('portal:all_members')
        
        elif action == 'update_support_needs':
            user_id = request.POST.get('user_id')
            support_needs = request.POST.get('support_needs', '').strip()
            
            try:
                member = get_object_or_404(User, id=user_id)
                member.support_needs = support_needs
                member.save()
                messages.success(request, f"Support needs updated for {member.name or member.username}.")
            except Exception as e:
                messages.error(request, f"Error updating support needs: {str(e)}")
            
            # Preserve course filter when redirecting
            course_filter = request.POST.get('course_filter', '')
            redirect_url = 'portal:all_members'
            if course_filter:
                from django.urls import reverse
                redirect_url = reverse('portal:all_members') + f'?course={course_filter}'
                return redirect(redirect_url)
            return redirect('portal:all_members')
        
        elif action == 'assign_buddy':
            from .models import BuddyAssignment
            member_id = request.POST.get('member_id')
            volunteer_id = request.POST.get('volunteer_id', '').strip()
            enrollment_id = request.POST.get('enrollment_id')
            
            try:
                enrollment = get_object_or_404(Enrollment, enrollment_id=enrollment_id)
                member = enrollment.user
                program = enrollment.program
                
                # If volunteer_id is empty, remove the buddy assignment
                if not volunteer_id:
                    deleted_count, _ = BuddyAssignment.objects.filter(
                        program=program,
                        member_user=member
                    ).delete()
                    if deleted_count > 0:
                        messages.success(request, f"Removed buddy assignment for {member.name}.")
                else:
                    volunteer = get_object_or_404(User, id=volunteer_id)
                    
                    # Create or update buddy assignment
                    assignment, created = BuddyAssignment.objects.update_or_create(
                        program=program,
                        member_user=member,
                        defaults={'volunteer_user': volunteer}
                    )
                    
                    if created:
                        messages.success(request, f"Assigned {volunteer.name} as buddy for {member.name}.")
                    else:
                        messages.success(request, f"Updated buddy assignment for {member.name} to {volunteer.name}.")
            except Exception as e:
                messages.error(request, f"Error managing buddy assignment: {str(e)}")
            
            # Preserve course filter when redirecting
            course_filter = request.POST.get('course_filter', '')
            redirect_url = 'portal:all_members'
            if course_filter:
                from django.urls import reverse
                redirect_url = reverse('portal:all_members') + f'?course={course_filter}'
                return redirect(redirect_url)
            return redirect('portal:all_members')
    
    # Get course filter from query params
    course_filter = request.GET.get('course', '').strip()
    
    # Get all members ordered by name with prefetched enrollment data
    members_query = User.objects.filter(role='member').prefetch_related(
        'enrollments__program'
    )
    
    # Apply course filter if provided
    filtered_program = None
    if course_filter:
        members_query = members_query.filter(
            enrollments__program__program_id=course_filter
        ).distinct()
        # Get the program object for the filter
        try:
            filtered_program = Program.objects.get(program_id=course_filter)
        except Program.DoesNotExist:
            pass
    
    members = members_query.order_by('name')
    
    # If filtering by course, get the enrollment for each member in that course
    course_enrollments = {}
    if course_filter and filtered_program:
        enrollments = Enrollment.objects.filter(
            program=filtered_program,
            user__in=members
        ).select_related('user')
        for enrollment in enrollments:
            course_enrollments[enrollment.user.id] = enrollment
    
    # Check if user can edit (managers can, PCMs cannot)
    can_edit = request.user.role == 'manager'
    
    # Get users with active OPDs (for all managers and PCMs to see status indicator)
    users_with_active_opd = set()
    from inclusive_world_portal.portal.models import DocumentExport
    active_exports = DocumentExport.objects.filter(
        is_active=True,
        user__in=members
    ).values_list('user_id', flat=True)
    users_with_active_opd = set(active_exports)
    
    # Build program volunteers mapping and buddy assignments for the enrollments partial
    program_volunteers = {}
    buddy_map = {}
    
    if can_edit:
        # Get all unique programs that members are enrolled in
        program_ids = set()
        for member in members:
            for enrollment in member.enrollments.all():
                program_ids.add(enrollment.program.program_id)
        
        # For each program, get approved volunteers
        for program_id in program_ids:
            volunteers = User.objects.filter(
                role__in=['volunteer', 'manager', 'person_centered_manager'],
                enrollments__program__program_id=program_id,
                enrollments__status=EnrollmentStatus.APPROVED
            ).distinct().order_by('name')
            program_volunteers[str(program_id)] = list(volunteers)
        
        # Get all buddy assignments for these members
        from .models import BuddyAssignment
        buddy_assignments = BuddyAssignment.objects.filter(
            member_user__in=members
        ).select_related('volunteer_user', 'program')
        
        # Build buddy_map keyed by (program_id, member_id) tuple
        for assignment in buddy_assignments:
            key = (str(assignment.program.program_id), assignment.member_user_id)
            buddy_map[key] = assignment.volunteer_user_id
    
    # Get all available programs for filter dropdown
    all_programs = Program.objects.filter(archived=False).order_by('name')
    
    context = {
        'members': members,
        'can_edit': can_edit,
        'status_choices': User.Status.choices,
        'users_with_active_opd': users_with_active_opd,
        'enrollment_statuses': EnrollmentStatus.choices,
        'program_volunteers': program_volunteers,
        'buddy_map': buddy_map,
        'enrollment_user_role': 'member',
        'all_programs': all_programs,
        'course_filter': course_filter,
        'filtered_program': filtered_program,
        'course_enrollments': course_enrollments,
    }
    
    return render(request, 'portal/all_members.html', context)


@login_required
def all_volunteers_view(request):
    """
    Display all volunteers (including managers and PCMs) across all programs.
    Shows Name (with profile link), Status (changeable dropdown), and Role (assignable by managers).
    Accessible to managers and person-centered managers.
    Note: Volunteers cannot be changed to members from this view.
    """
    # Check if user is a manager or person-centered manager
    if request.user.role not in ['manager', 'person_centered_manager']:
        messages.error(request, "This page is only accessible to managers and person-centered managers.")
        return redirect('home')
    
    from inclusive_world_portal.users.models import User
    from django.db.models import Q
    
    # Handle POST requests for role/status updates (managers only)
    if request.method == 'POST' and request.user.role == 'manager':
        action = request.POST.get('action')
        
        if action == 'update_role':
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('role')
            
            try:
                volunteer = get_object_or_404(User, id=user_id)
                
                # Validate role - managers can assign volunteer, manager, or PCM roles (not member)
                valid_roles = ['volunteer', 'person_centered_manager', 'manager']
                if new_role in valid_roles:
                    volunteer.role = new_role
                    volunteer.save()
                    messages.success(request, f"Role updated for {volunteer.name or volunteer.username}.")
                else:
                    messages.error(request, "Invalid role selection.")
            except Exception as e:
                messages.error(request, f"Error updating role: {str(e)}")
            
            # Preserve course filter when redirecting
            course_filter = request.POST.get('course_filter', '')
            redirect_url = 'portal:all_volunteers'
            if course_filter:
                from django.urls import reverse
                redirect_url = reverse('portal:all_volunteers') + f'?course={course_filter}'
                return redirect(redirect_url)
            return redirect('portal:all_volunteers')
        
        elif action == 'update_status':
            user_id = request.POST.get('user_id')
            new_status = request.POST.get('status')
            
            try:
                volunteer = get_object_or_404(User, id=user_id)
                
                # Validate status
                valid_statuses = [choice[0] for choice in User.Status.choices]
                if new_status in valid_statuses:
                    volunteer.status = new_status
                    volunteer.save()
                    messages.success(request, f"Status updated for {volunteer.name or volunteer.username}.")
                else:
                    messages.error(request, "Invalid status selection.")
            except Exception as e:
                messages.error(request, f"Error updating status: {str(e)}")
            
            # Preserve course filter when redirecting
            course_filter = request.POST.get('course_filter', '')
            redirect_url = 'portal:all_volunteers'
            if course_filter:
                from django.urls import reverse
                redirect_url = reverse('portal:all_volunteers') + f'?course={course_filter}'
                return redirect(redirect_url)
            return redirect('portal:all_volunteers')
        
        elif action == 'update_enrollment_status':
            enrollment_id = request.POST.get('enrollment_id')
            new_status = request.POST.get('enrollment_status')
            
            try:
                enrollment = get_object_or_404(Enrollment, enrollment_id=enrollment_id)
                
                # Validate status
                valid_statuses = [choice[0] for choice in EnrollmentStatus.choices]
                if new_status in valid_statuses:
                    old_status = enrollment.status
                    enrollment.status = new_status
                    enrollment.assigned_by = request.user
                    enrollment.assigned_at = timezone.now()
                    enrollment.save()
                    
                    # Update program enrolled count if status changed to/from approved
                    program = enrollment.program
                    if old_status != EnrollmentStatus.APPROVED and new_status == EnrollmentStatus.APPROVED:
                        program.enrolled += 1
                        program.save()
                    elif old_status == EnrollmentStatus.APPROVED and new_status != EnrollmentStatus.APPROVED:
                        program.enrolled = max(0, program.enrolled - 1)
                        program.save()
                    
                    messages.success(request, f"Enrollment status updated for {enrollment.user.name or enrollment.user.username}.")
                else:
                    messages.error(request, "Invalid enrollment status selection.")
            except Exception as e:
                messages.error(request, f"Error updating enrollment status: {str(e)}")
            
            # Preserve course filter when redirecting
            course_filter = request.POST.get('course_filter', '')
            redirect_url = 'portal:all_volunteers'
            if course_filter:
                from django.urls import reverse
                redirect_url = reverse('portal:all_volunteers') + f'?course={course_filter}'
                return redirect(redirect_url)
            return redirect('portal:all_volunteers')
        
        elif action == 'toggle_volunteer_lead':
            volunteer_id = request.POST.get('volunteer_id')
            program_id = request.POST.get('program_id')
            is_lead = request.POST.get('is_lead') == 'true'
            
            try:
                from inclusive_world_portal.portal.models import ProgramVolunteerLead
                volunteer = get_object_or_404(User, id=volunteer_id)
                program = get_object_or_404(Program, program_id=program_id)
                
                if is_lead:
                    # Add volunteer as lead if not already
                    ProgramVolunteerLead.objects.get_or_create(
                        program=program,
                        volunteer=volunteer
                    )
                    messages.success(request, f"{volunteer.name or volunteer.username} is now a volunteer lead for {program.name}.")
                else:
                    # Remove volunteer lead status
                    ProgramVolunteerLead.objects.filter(
                        program=program,
                        volunteer=volunteer
                    ).delete()
                    messages.success(request, f"{volunteer.name or volunteer.username} is no longer a volunteer lead for {program.name}.")
            except Exception as e:
                messages.error(request, f"Error updating volunteer lead status: {str(e)}")
            
            # Preserve course filter when redirecting
            course_filter = request.POST.get('course_filter', '')
            redirect_url = 'portal:all_volunteers'
            if course_filter:
                from django.urls import reverse
                redirect_url = reverse('portal:all_volunteers') + f'?course={course_filter}'
                return redirect(redirect_url)
            return redirect('portal:all_volunteers')
    
    # Get course filter from query params
    course_filter = request.GET.get('course', '').strip()
    
    # Get all volunteers, managers, and person-centered managers ordered by name with prefetched enrollment data
    volunteers_query = User.objects.filter(
        role__in=['volunteer', 'manager', 'person_centered_manager']
    ).prefetch_related(
        'enrollments__program'
    )
    
    # Apply course filter if provided
    filtered_program = None
    if course_filter:
        volunteers_query = volunteers_query.filter(
            enrollments__program__program_id=course_filter
        ).distinct()
        # Get the program object for the filter
        try:
            filtered_program = Program.objects.get(program_id=course_filter)
        except Program.DoesNotExist:
            pass
    
    volunteers = volunteers_query.order_by('name')
    
    # If filtering by course, get the enrollment for each volunteer in that course
    course_enrollments = {}
    if course_filter and filtered_program:
        enrollments = Enrollment.objects.filter(
            program=filtered_program,
            user__in=volunteers
        ).select_related('user')
        for enrollment in enrollments:
            course_enrollments[enrollment.user.id] = enrollment
    
    # Check if user can edit (managers can, PCMs cannot)
    can_edit = request.user.role == 'manager'
    
    # Volunteer-only role choices (excluding member)
    volunteer_role_choices = [
        ('volunteer', 'Volunteer'),
        ('person_centered_manager', 'Person Centered Manager'),
        ('manager', 'Manager'),
    ]
    
    # Get users with active OPDs (for all managers and PCMs to see status indicator)
    users_with_active_opd = set()
    from inclusive_world_portal.portal.models import DocumentExport
    active_exports = DocumentExport.objects.filter(
        is_active=True,
        user__in=volunteers
    ).values_list('user_id', flat=True)
    users_with_active_opd = set(active_exports)
    
    # Get all available programs for filter dropdown
    all_programs = Program.objects.filter(archived=False).order_by('name')
    
    # Get volunteer leads for the filtered program if applicable
    volunteer_leads = set()
    if course_filter and filtered_program:
        from inclusive_world_portal.portal.models import ProgramVolunteerLead
        lead_user_ids = ProgramVolunteerLead.objects.filter(
            program=filtered_program
        ).values_list('volunteer_id', flat=True)
        volunteer_leads = set(lead_user_ids)
    
    # Note: Volunteers don't need buddy assignments, so we don't build those maps
    # We still pass enrollment_statuses for the status dropdown
    context = {
        'volunteers': volunteers,
        'can_edit': can_edit,
        'role_choices': volunteer_role_choices if can_edit else [],
        'status_choices': User.Status.choices,
        'users_with_active_opd': users_with_active_opd,
        'enrollment_statuses': EnrollmentStatus.choices,
        'program_volunteers': {},  # Empty since volunteers don't have buddies
        'buddy_map': {},  # Empty since volunteers don't have buddies
        'enrollment_user_role': 'volunteer',
        'all_programs': all_programs,
        'course_filter': course_filter,
        'filtered_program': filtered_program,
        'course_enrollments': course_enrollments,
        'volunteer_leads': volunteer_leads,
    }
    
    return render(request, 'portal/all_volunteers.html', context)


# -------------------------
# AJAX endpoints for enrollment management
# -------------------------

@login_required
@require_http_methods(["POST"])
def ajax_update_enrollment_status(request):
    """
    AJAX endpoint to update enrollment status.
    Only accessible to managers.
    """
    if request.user.role != 'manager':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        enrollment_id = request.POST.get('enrollment_id')
        new_status = request.POST.get('status')
        
        enrollment = get_object_or_404(Enrollment, enrollment_id=enrollment_id)
        
        # Validate status
        valid_statuses = [choice[0] for choice in EnrollmentStatus.choices]
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        old_status = enrollment.status
        enrollment.status = new_status
        enrollment.assigned_by = request.user
        enrollment.assigned_at = timezone.now()
        enrollment.save()
        
        # Update program enrolled count if status changed to/from approved
        program = enrollment.program
        if old_status != EnrollmentStatus.APPROVED and new_status == EnrollmentStatus.APPROVED:
            program.enrolled += 1
            program.save()
        elif old_status == EnrollmentStatus.APPROVED and new_status != EnrollmentStatus.APPROVED:
            program.enrolled = max(0, program.enrolled - 1)
            program.save()
        
        return JsonResponse({
            'success': True,
            'status': new_status,
            'status_display': enrollment.get_status_display()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def ajax_update_buddy_assignment(request):
    """
    AJAX endpoint to update buddy assignment for a member in a program.
    Only accessible to managers.
    """
    if request.user.role != 'manager':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        enrollment_id = request.POST.get('enrollment_id')
        volunteer_id = request.POST.get('volunteer_id', '').strip()
        
        from inclusive_world_portal.users.models import User
        
        enrollment = get_object_or_404(Enrollment, enrollment_id=enrollment_id)
        member = enrollment.user
        program = enrollment.program
        
        # Verify the user is a member
        if member.role != 'member':
            return JsonResponse({'error': 'Buddy assignments are only for members'}, status=400)
        
        # If volunteer_id is empty, remove the buddy assignment
        if not volunteer_id:
            deleted_count, _ = BuddyAssignment.objects.filter(
                program=program,
                member_user=member
            ).delete()
            return JsonResponse({
                'success': True,
                'buddy_name': None,
                'message': 'Buddy assignment removed'
            })
        
        # Validate the volunteer is enrolled in the program
        volunteer = get_object_or_404(User, id=volunteer_id)
        volunteer_enrollment = Enrollment.objects.filter(
            program=program,
            user=volunteer,
            status=EnrollmentStatus.APPROVED
        ).first()
        
        if not volunteer_enrollment:
            return JsonResponse({'error': 'Selected volunteer is not enrolled in this program'}, status=400)
        
        # Create or update buddy assignment
        assignment, created = BuddyAssignment.objects.update_or_create(
            program=program,
            member_user=member,
            defaults={'volunteer_user': volunteer}
        )
        
        return JsonResponse({
            'success': True,
            'buddy_name': volunteer.name or volunteer.username,
            'message': 'Buddy assignment updated'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
