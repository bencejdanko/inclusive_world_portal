"""
Notification views for managing and displaying user notifications.
Uses django-notifications-hq for the notification system.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import ListView, FormView
from django.urls import reverse_lazy
from notifications.models import Notification
from notifications.signals import notify

from inclusive_world_portal.users.models import User
from inclusive_world_portal.portal.models import Program
from .notification_forms import BulkNotificationForm


class NotificationListView(LoginRequiredMixin, ListView):
    """
    Display all notifications for the logged-in user.
    Supports filtering by read/unread status.
    """
    template_name = 'users/notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        qs = user.notifications.all()
        
        # Filter by status
        status = self.request.GET.get('status', 'all')
        if status == 'unread':
            qs = qs.unread()
        elif status == 'read':
            qs = qs.read()
        
        return qs.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = self.request.user.notifications.unread().count()
        context['current_status'] = self.request.GET.get('status', 'all')
        return context


@login_required
def notification_detail(request, notification_id):
    """
    Display a single notification and mark it as read.
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    
    # Mark as read
    notification.mark_as_read()
    
    context = {
        'notification': notification,
    }
    
    return render(request, 'users/notifications/notification_detail.html', context)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """
    Mark a single notification as read via AJAX.
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    
    notification.mark_as_read()
    
    if request.headers.get('HX-Request'):
        # HTMX request
        return render(request, 'users/notifications/partials/notification_item.html', {
            'notification': notification
        })
    
    # Regular form submission - redirect back to notification list
    return redirect('users:notification_list')


@login_required
@require_POST
def mark_notification_unread(request, notification_id):
    """
    Mark a single notification as unread via AJAX.
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    
    notification.mark_as_unread()
    
    if request.headers.get('HX-Request'):
        # HTMX request
        return render(request, 'users/notifications/partials/notification_item.html', {
            'notification': notification
        })
    
    # Regular form submission - redirect back to notification list
    return redirect('users:notification_list')


@login_required
@require_POST
def mark_all_read(request):
    """
    Mark all unread notifications as read for the current user.
    """
    request.user.notifications.unread().mark_all_as_read()
    messages.success(request, 'All notifications marked as read.')
    
    if request.headers.get('HX-Request'):
        return redirect('users:notification_list')
    
    return redirect('users:notification_list')


@login_required
@require_POST
def delete_notification(request, notification_id):
    """
    Delete a notification.
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    
    notification.delete()
    messages.success(request, 'Notification deleted.')
    
    # Always redirect back to notification list
    return redirect('users:notification_list')


class CreateBulkNotificationView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """
    Manager-only view for creating bulk notifications.
    Allows sending notifications to specific users, roles, or programs.
    """
    template_name = 'users/notifications/create_notification.html'
    form_class = BulkNotificationForm
    success_url = reverse_lazy('users:notification_list')
    
    def test_func(self):
        """Only managers can create bulk notifications."""
        return self.request.user.role == User.Role.MANAGER
    
    def form_valid(self, form):
        """
        Send notifications based on the form data.
        """
        verb = form.cleaned_data['verb']
        description = form.cleaned_data['description']
        level = form.cleaned_data['level']
        
        # Determine recipients
        recipients = []
        
        # Add users by role
        target_roles = form.cleaned_data.get('target_roles', [])
        if target_roles:
            recipients.extend(
                User.objects.filter(role__in=target_roles, status=User.Status.ACTIVE)
            )
        
        # Add users by program
        target_programs = form.cleaned_data.get('target_programs', [])
        if target_programs:
            # Get users enrolled in these programs
            from inclusive_world_portal.portal.models import Enrollment
            program_users = User.objects.filter(
                enrollments__program__in=target_programs,
                enrollments__status='approved'
            ).distinct()
            recipients.extend(program_users)
        
        # Add specific users
        target_users = form.cleaned_data.get('target_users', [])
        if target_users:
            recipients.extend(target_users)
        
        # Remove duplicates
        recipients = list(set(recipients))
        # Ensure requester is included if they selected their own role and are active
        if target_roles and self.request.user.role in target_roles and self.request.user.status == User.Status.ACTIVE:
            if self.request.user not in recipients:
                recipients.append(self.request.user)
        
        if not recipients:
            messages.error(self.request, 'No recipients selected.')
            return self.form_invalid(form)
        
        # Send notification to all recipients
        for recipient in recipients:
            notify.send(
                sender=self.request.user,
                recipient=recipient,
                verb=verb,
                description=description,
                level=level,
            )
        
        messages.success(
            self.request,
            f'Notification sent to {len(recipients)} user(s).'
        )
        
        return super().form_valid(form)


@login_required
def notification_api_unread_count(request):
    """
    API endpoint that returns the unread notification count.
    Used for live updating the notification badge.
    """
    unread_count = request.user.notifications.unread().count()
    return JsonResponse({'unread_count': unread_count})


@login_required
def notification_api_unread_list(request):
    """
    API endpoint that returns the list of unread notifications.
    Supports max parameter to limit results.
    """
    max_items = int(request.GET.get('max', 5))
    mark_as_read = request.GET.get('mark_as_read', '').lower() == 'true'
    
    notifications = request.user.notifications.unread()[:max_items]
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'actor': str(notification.actor) if notification.actor else '',
            'verb': notification.verb,
            'description': notification.description or '',
            'timestamp': notification.timestamp.isoformat(),
            'level': notification.level,
            'unread': notification.unread,
        })
        
        if mark_as_read:
            notification.mark_as_read()
    
    return JsonResponse({
        'unread_count': request.user.notifications.unread().count(),
        'unread_list': notifications_data,
    })


# Export views
notification_list_view = NotificationListView.as_view()
create_bulk_notification_view = CreateBulkNotificationView.as_view()
