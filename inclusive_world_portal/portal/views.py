"""
Views for the portal app - Program enrollment and management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import stripe

from .models import Program, Enrollment, Payment

stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else None


@login_required
def program_catalog_view(request):
    """
    Display catalog of available programs for enrollment.
    Only accessible to users with complete profile and survey.
    """
    # Check if user can purchase programs
    if not request.user.can_purchase_programs:
        messages.warning(
            request,
            "Please complete your profile and discovery survey before browsing programs."
        )
        return redirect('users:survey_start')
    
    # Get all active (non-archived) programs
    programs = Program.objects.filter(archived=False).order_by('name')
    
    # Get user's existing enrollments to mark already enrolled programs
    enrolled_program_ids = request.user.enrollments.values_list('program_id', flat=True)
    
    context = {
        'programs': programs,
        'enrolled_program_ids': list(enrolled_program_ids),
    }
    
    return render(request, 'portal/program_catalog.html', context)


@login_required
def program_detail_view(request, program_id):
    """
    Display detailed information about a specific program.
    Can be used for the info icon modal/page.
    """
    program = get_object_or_404(Program, program_id=program_id, archived=False)
    
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
            'image_uri': program.image_uri,
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
    if not request.user.can_purchase_programs:
        messages.warning(
            request,
            "Please complete your profile and discovery survey before enrolling in programs."
        )
        return redirect('users:survey_start')
    
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
    if not request.user.can_purchase_programs:
        messages.warning(request, "Please complete your profile and discovery survey first.")
        return redirect('users:survey_start')
    
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
