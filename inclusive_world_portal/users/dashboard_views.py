"""
Dashboard views for different user roles.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages

from inclusive_world_portal.users.models import User


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view that redirects to role-specific dashboards.
    """
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Redirect based on user role
        if user.role == User.Role.MEMBER:
            return redirect('users:member_dashboard')
        elif user.role == User.Role.VOLUNTEER:
            return redirect('users:volunteer_dashboard')
        elif user.role == User.Role.PERSON_CENTERED_MANAGER:
            return redirect('users:pcm_dashboard')
        elif user.role == User.Role.MANAGER:
            return redirect('users:manager_dashboard')
        elif user.role == User.Role.ADMIN:
            return redirect('users:admin_dashboard')
        else:
            messages.warning(request, "Your account role is not configured. Please contact support.")
            return redirect('home')


class MemberDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for members.
    """
    template_name = 'users/dashboards/member_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add member-specific data
        context.update({
            'profile_complete': user.profile_is_complete,
            'survey_complete': user.survey_is_complete,
            'can_purchase': user.can_purchase_programs,
            # TODO: Add program enrollments
            # TODO: Add upcoming sessions
            # TODO: Add recent activities
        })
        
        return context


class VolunteerDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for volunteers.
    """
    template_name = 'users/dashboards/volunteer_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add volunteer-specific data
        context.update({
            # TODO: Add upcoming volunteer sessions
            # TODO: Add assigned members
            # TODO: Add training requirements
        })
        
        return context


class PersonCenteredManagerDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for person-centered managers.
    """
    template_name = 'users/dashboards/pcm_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add PCM-specific data
        context.update({
            # TODO: Add caseload
            # TODO: Add pending reviews
            # TODO: Add reports
        })
        
        return context


class ManagerDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for managers.
    """
    template_name = 'users/dashboards/manager_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add manager-specific data
        context.update({
            # TODO: Add organization stats
            # TODO: Add financial overview
            # TODO: Add staff overview
        })
        
        return context


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for admins.
    """
    template_name = 'users/dashboards/admin_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add admin-specific data
        context.update({
            'total_users': User.objects.count(),
            'total_members': User.objects.filter(role=User.Role.MEMBER).count(),
            'total_volunteers': User.objects.filter(role=User.Role.VOLUNTEER).count(),
            'total_staff': User.objects.filter(
                role__in=[User.Role.PERSON_CENTERED_MANAGER, User.Role.MANAGER, User.Role.ADMIN]
            ).count(),
        })
        
        return context


# Export views
dashboard_view = DashboardView.as_view()
member_dashboard_view = MemberDashboardView.as_view()
volunteer_dashboard_view = VolunteerDashboardView.as_view()
pcm_dashboard_view = PersonCenteredManagerDashboardView.as_view()
manager_dashboard_view = ManagerDashboardView.as_view()
admin_dashboard_view = AdminDashboardView.as_view()
