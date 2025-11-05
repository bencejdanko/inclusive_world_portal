"""
Navigation configuration for role-based sidebar menus.
"""
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


def get_navigation_items(user):
    """
    Returns navigation items based on user role.
    Each item is a dict with 'label', 'url', 'icon_class', and optionally 'badge'.
    """
    if not user.is_authenticated:
        return []
    
    role = user.role
    
    # Common items for all roles
    common_items = []
    
    # Member navigation
    if role == 'member':
        # Determine registration status for better UI feedback
        from inclusive_world_portal.portal.models import EnrollmentSettings
        
        enrollment_settings = EnrollmentSettings.get_settings()
        forms_complete = user.forms_are_complete
        enrollment_open = enrollment_settings.enrollment_open
        can_register = user.can_purchase_programs
        
        # Determine registration status and message
        if can_register:
            # Forms complete and enrollment open
            registration_status = 'open'
            registration_url = reverse('portal:program_catalog')
            registration_tooltip = _('Registration is open')
        elif not forms_complete:
            # Forms incomplete
            registration_status = 'closed_forms'
            registration_url = reverse('users:survey_start')
            registration_tooltip = _('Complete your profile and discovery questions to register')
        else:
            # Forms complete but enrollment closed
            registration_status = 'closed_season'
            registration_url = '#'
            registration_tooltip = enrollment_settings.closure_reason or _('Registration is currently closed')
        
        nav_items = [
            {
                'label': _('Dashboard'),
                'url': reverse('users:member_dashboard'),
                'icon_class': 'bi bi-house-door',
            },
            {
                'label': _('One Page Description'),
                'url': reverse('users:view_active_opd'),
                'icon_class': 'bi bi-file-earmark-text',
            },
            {
                'label': _('Profile'),
                'url': reverse('users:detail', kwargs={'username': user.username}),
                'icon_class': 'bi bi-person-circle',
                'show_completion': True,
                'is_complete': user.profile_is_complete,
            },
            {
                'label': _('Discovery Questions'),
                'url': reverse('users:survey_start'),
                'icon_class': 'bi bi-clipboard-check',
                'show_completion': True,
                'is_complete': user.survey_is_complete,
            },
            {
                'label': _('Registration'),
                'url': registration_url,
                'icon_class': 'bi bi-grid-3x3-gap',
                'registration_status': registration_status,  # 'open', 'closed_forms', or 'closed_season'
                'registration_tooltip': registration_tooltip,
                'show_status_indicator': True,
            },
            {
                'label': _('My Programs'),
                'url': reverse('portal:my_programs'),
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('My Attendance'),
                'url': reverse('portal:my_attendance'),
                'icon_class': 'bi bi-calendar-check',
            },
        ]
        return nav_items
    
    # Volunteer navigation - Same as member but without payment requirements
    elif role == 'volunteer':
        # Determine registration status for better UI feedback
        from inclusive_world_portal.portal.models import EnrollmentSettings
        
        enrollment_settings = EnrollmentSettings.get_settings()
        forms_complete = user.forms_are_complete
        enrollment_open = enrollment_settings.enrollment_open
        
        # Volunteers can register if forms are complete and enrollment is open (no payment needed)
        can_register = forms_complete and enrollment_open
        
        # Determine registration status and message
        if can_register:
            # Forms complete and enrollment open
            registration_status = 'open'
            registration_url = reverse('portal:volunteer_program_catalog')
            registration_tooltip = _('Registration is open')
        elif not forms_complete:
            # Forms incomplete
            registration_status = 'closed_forms'
            registration_url = reverse('users:survey_start')
            registration_tooltip = _('Complete your profile and discovery questions to register')
        else:
            # Forms complete but enrollment closed
            registration_status = 'closed_season'
            registration_url = '#'
            registration_tooltip = enrollment_settings.closure_reason or _('Registration is currently closed')
        
        nav_items = [
            {
                'label': _('Dashboard'),
                'url': reverse('users:volunteer_dashboard'),
                'icon_class': 'bi bi-house-door',
            },
            {
                'label': _('One Page Description'),
                'url': reverse('users:view_active_opd'),
                'icon_class': 'bi bi-file-earmark-text',
            },
            {
                'label': _('Profile'),
                'url': reverse('users:detail', kwargs={'username': user.username}),
                'icon_class': 'bi bi-person-circle',
                'show_completion': True,
                'is_complete': user.profile_is_complete,
            },
            {
                'label': _('Discovery Questions'),
                'url': reverse('users:survey_start'),
                'icon_class': 'bi bi-clipboard-check',
                'show_completion': True,
                'is_complete': user.survey_is_complete,
            },
            {
                'label': _('Registration'),
                'url': registration_url,
                'icon_class': 'bi bi-grid-3x3-gap',
                'registration_status': registration_status,  # 'open', 'closed_forms', or 'closed_season'
                'registration_tooltip': registration_tooltip,
                'show_status_indicator': True,
            },
            {
                'label': _('My Programs'),
                'url': reverse('portal:my_programs'),
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('My Attendance'),
                'url': reverse('portal:my_attendance'),
                'icon_class': 'bi bi-calendar-check',
            },
        ]
        return nav_items
    
    # Person Centered Manager navigation - Same as manager with program registration capability
    elif role == 'person_centered_manager':
        # Determine registration status for better UI feedback
        from inclusive_world_portal.portal.models import EnrollmentSettings
        
        enrollment_settings = EnrollmentSettings.get_settings()
        forms_complete = user.forms_are_complete
        enrollment_open = enrollment_settings.enrollment_open
        
        # Person-centered managers can register if forms are complete and enrollment is open (no payment needed)
        can_register = forms_complete and enrollment_open
        
        # Determine registration status and message
        if can_register:
            # Forms complete and enrollment open
            registration_status = 'open'
            registration_url = reverse('portal:volunteer_program_catalog')
            registration_tooltip = _('Registration is open')
        elif not forms_complete:
            # Forms incomplete
            registration_status = 'closed_forms'
            registration_url = reverse('users:survey_start')
            registration_tooltip = _('Complete your profile and discovery questions to register')
        else:
            # Forms complete but enrollment closed
            registration_status = 'closed_season'
            registration_url = '#'
            registration_tooltip = enrollment_settings.closure_reason or _('Registration is currently closed')
        
        return [
            {
                'label': _('Dashboard'),
                'url': reverse('users:pcm_dashboard'),
                'icon_class': 'bi bi-house-door',
            },
            {
                'label': _('One Page Description'),
                'url': reverse('users:view_active_opd'),
                'icon_class': 'bi bi-file-earmark-text',
            },
            {
                'label': _('Profile'),
                'url': reverse('users:detail', kwargs={'username': user.username}),
                'icon_class': 'bi bi-person-circle',
                'show_completion': True,
                'is_complete': user.profile_is_complete,
            },
            {
                'label': _('Discovery Questions'),
                'url': reverse('users:survey_start'),
                'icon_class': 'bi bi-clipboard-check',
                'show_completion': True,
                'is_complete': user.survey_is_complete,
            },
            {
                'label': _('Registration'),
                'url': registration_url,
                'icon_class': 'bi bi-grid-3x3-gap',
                'registration_status': registration_status,  # 'open', 'closed_forms', or 'closed_season'
                'registration_tooltip': registration_tooltip,
                'show_status_indicator': True,
            },
            {
                'label': _('My Programs'),
                'url': reverse('portal:my_programs'),
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('My Attendance'),
                'url': reverse('portal:my_attendance'),
                'icon_class': 'bi bi-calendar-check',
            },
            {
                'label': _('All Members'),
                'url': reverse('portal:all_members'),
                'icon_class': 'bi bi-people',
            },
            {
                'label': _('All Volunteers'),
                'url': reverse('portal:all_volunteers'),
                'icon_class': 'bi bi-people-fill',
            },
            {
                'label': _('Reports'),
                'url': '#',
                'icon_class': 'bi bi-file-earmark-bar-graph',
            },
        ]
    
    # Manager navigation - Same as volunteer but with additional Manage Programs option
    elif role == 'manager':
        # Determine registration status for better UI feedback
        from inclusive_world_portal.portal.models import EnrollmentSettings
        
        enrollment_settings = EnrollmentSettings.get_settings()
        forms_complete = user.forms_are_complete
        enrollment_open = enrollment_settings.enrollment_open
        
        # Managers can register if forms are complete and enrollment is open (no payment needed)
        can_register = forms_complete and enrollment_open
        
        # Determine registration status and message
        if can_register:
            # Forms complete and enrollment open
            registration_status = 'open'
            registration_url = reverse('portal:volunteer_program_catalog')
            registration_tooltip = _('Registration is open')
        elif not forms_complete:
            # Forms incomplete
            registration_status = 'closed_forms'
            registration_url = reverse('users:survey_start')
            registration_tooltip = _('Complete your profile and discovery questions to register')
        else:
            # Forms complete but enrollment closed
            registration_status = 'closed_season'
            registration_url = '#'
            registration_tooltip = enrollment_settings.closure_reason or _('Registration is currently closed')
        
        nav_items = [
            {
                'label': _('Dashboard'),
                'url': reverse('users:manager_dashboard'),
                'icon_class': 'bi bi-house-door',
            },
            {
                'label': _('One Page Description'),
                'url': reverse('users:view_active_opd'),
                'icon_class': 'bi bi-file-earmark-text',
            },
            {
                'label': _('Profile'),
                'url': reverse('users:detail', kwargs={'username': user.username}),
                'icon_class': 'bi bi-person-circle',
                'show_completion': True,
                'is_complete': user.profile_is_complete,
            },
            {
                'label': _('Discovery Questions'),
                'url': reverse('users:survey_start'),
                'icon_class': 'bi bi-clipboard-check',
                'show_completion': True,
                'is_complete': user.survey_is_complete,
            },
            {
                'label': _('Registration'),
                'url': registration_url,
                'icon_class': 'bi bi-grid-3x3-gap',
                'registration_status': registration_status,  # 'open', 'closed_forms', or 'closed_season'
                'registration_tooltip': registration_tooltip,
                'show_status_indicator': True,
            },
            {
                'label': _('My Programs'),
                'url': reverse('portal:my_programs'),
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('My Attendance'),
                'url': reverse('portal:my_attendance'),
                'icon_class': 'bi bi-calendar-check',
            },
            {
                'label': _('All Members'),
                'url': reverse('portal:all_members'),
                'icon_class': 'bi bi-people',
            },
            {
                'label': _('All Volunteers'),
                'url': reverse('portal:all_volunteers'),
                'icon_class': 'bi bi-people-fill',
            },
            {
                'label': _('Manage Programs'),
                'url': reverse('portal:manager_programs'),
                'icon_class': 'bi bi-gear-wide-connected',
            },
        ]
        return nav_items
    
    # Admin navigation
    elif role == 'admin':
        return [
            {
                'label': _('Dashboard'),
                'url': reverse('home'),
                'icon_class': 'bi bi-house-door',
            },
            {
                'label': _('All Users'),
                'url': '#',
                'icon_class': 'bi bi-people',
            },
            {
                'label': _('One Page Description'),
                'url': reverse('users:view_active_opd'),
                'icon_class': 'bi bi-file-earmark-text',
            },
            {
                'label': _('Programs'),
                'url': '#',
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('Admin Panel'),
                'url': reverse('admin:index'),
                'icon_class': 'bi bi-shield-lock',
            },
            {
                'label': _('System Settings'),
                'url': '#',
                'icon_class': 'bi bi-gear',
            },
        ]
    
    return common_items


def navigation_context(request):
    """
    Context processor to add navigation items to all templates.
    """
    nav_items = []
    role_display = None
    
    if request.user.is_authenticated:
        nav_items = get_navigation_items(request.user)
        role_display = request.user.get_role_display()
    
    return {
        'nav_items': nav_items,
        'user_role_display': role_display,
    }
