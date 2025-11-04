"""
Views for fees and purchased programs display.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q

from .models import Enrollment, Payment, Program


@login_required
def fees_overview_view(request):
    """
    Display user's purchased programs/enrollments with fees and payment information.
    Shows enrolled programs with their status, fees, and payment details.
    """
    user = request.user
    
    # Get all enrollments for the user with related program data
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
    }
    
    return render(request, 'portal/fees.html', context)
