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
        enrollment_open = enrollment_settings.enrollment_open
        can_register = user.can_purchase_programs
        
        # Determine registration status and message
        meets_requirements, missing_items = user.enrollment_requirements_status
        
        if can_register:
            # Requirements met and enrollment open
            registration_status = 'open'
            registration_url = reverse('portal:program_catalog')
            registration_tooltip = _('Registration is open')
        elif not meets_requirements:
            # Requirements not met
            registration_status = 'closed_forms'
            registration_url = reverse('users:detail', kwargs={'username': user.username})
            registration_tooltip = _(f'Complete requirements: {", ".join(missing_items)}')
        else:
            # Requirements met but enrollment closed
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
                'label': _('Notifications'),
                'url': reverse('users:notification_list'),
                'icon_class': 'bi bi-bell',
                'show_notification_badge': True,
            },
            {
                'label': _('Documents'),
                'url': reverse('users:document_list'),
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
                'label': _('Registration'),
                'url': registration_url,
                'icon_class': 'bi bi-grid-3x3-gap',
                'registration_status': registration_status,  # 'open', 'closed_forms', or 'closed_season'
                'registration_tooltip': registration_tooltip,
                'show_status_indicator': True,
            },
            {
                'label': _('Programs'),
                'url': reverse('portal:programs'),
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('My Attendance'),
                'url': reverse('portal:my_attendance'),
                'icon_class': 'bi bi-calendar-check',
            },
            {
                'label': _('Tasks'),
                'url': '/surveys',
                'icon_class': 'bi bi-file-earmark-bar-graph',
            },
        ]
        return nav_items
    
    # Volunteer navigation - Same as member but without payment requirements
    elif role == 'volunteer':
        # Determine registration status for better UI feedback
        from inclusive_world_portal.portal.models import EnrollmentSettings, ProgramVolunteerLead
        
        enrollment_settings = EnrollmentSettings.get_settings()
        enrollment_open = enrollment_settings.enrollment_open
        meets_requirements, missing_items = user.enrollment_requirements_status
        
        # Volunteers can register if requirements are met and enrollment is open (no payment needed)
        can_register = meets_requirements and enrollment_open
        
        # Determine registration status and message
        if can_register:
            # Requirements met and enrollment open
            registration_status = 'open'
            registration_url = reverse('portal:volunteer_program_catalog')
            registration_tooltip = _('Registration is open')
        elif not meets_requirements:
            # Requirements not met
            registration_status = 'closed_forms'
            registration_url = reverse('users:detail', kwargs={'username': user.username})
            registration_tooltip = _(f'Complete requirements: {", ".join(missing_items)}')
        else:
            # Requirements met but enrollment closed
            registration_status = 'closed_season'
            registration_url = '#'
            registration_tooltip = enrollment_settings.closure_reason or _('Registration is currently closed')
        
        # Check if volunteer is a program lead
        is_program_lead = ProgramVolunteerLead.objects.filter(volunteer=user).exists()
        
        nav_items = [
            {
                'label': _('Dashboard'),
                'url': reverse('users:volunteer_dashboard'),
                'icon_class': 'bi bi-house-door',
            },
            {
                'label': _('Notifications'),
                'url': reverse('users:notification_list'),
                'icon_class': 'bi bi-bell',
                'show_notification_badge': True,
            },
            {
                'label': _('Documents'),
                'url': reverse('users:document_list'),
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
                'label': _('Registration'),
                'url': registration_url,
                'icon_class': 'bi bi-grid-3x3-gap',
                'registration_status': registration_status,  # 'open', 'closed_forms', or 'closed_season'
                'registration_tooltip': registration_tooltip,
                'show_status_indicator': True,
            },
            {
                'label': _('Programs'),
                'url': reverse('portal:programs'),
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('My Attendance'),
                'url': reverse('portal:my_attendance'),
                'icon_class': 'bi bi-calendar-check',
            },
        ]
        
        # Add Members and Volunteers navigation for program leads
        if is_program_lead:
            nav_items.extend([
                {
                    'label': _('Members'),
                    'url': reverse('portal:all_members'),
                    'icon_class': 'bi bi-people',
                },
                {
                    'label': _('Volunteers'),
                    'url': reverse('portal:all_volunteers'),
                    'icon_class': 'bi bi-people-fill',
                },
            ])
        
        nav_items.append({
            'label': _('Tasks'),
            'url': '/surveys',
            'icon_class': 'bi bi-file-earmark-bar-graph',
        })
        
        return nav_items
    
    # Person Centered Manager navigation - Same as manager with program registration capability
    elif role == 'person_centered_manager':
        # Determine registration status for better UI feedback
        from inclusive_world_portal.portal.models import EnrollmentSettings
        
        enrollment_settings = EnrollmentSettings.get_settings()
        enrollment_open = enrollment_settings.enrollment_open
        meets_requirements, missing_items = user.enrollment_requirements_status
        
        # Person-centered managers can register if requirements are met and enrollment is open (no payment needed)
        can_register = meets_requirements and enrollment_open
        
        # Determine registration status and message
        if can_register:
            # Requirements met and enrollment open
            registration_status = 'open'
            registration_url = reverse('portal:volunteer_program_catalog')
            registration_tooltip = _('Registration is open')
        elif not meets_requirements:
            # Requirements not met
            registration_status = 'closed_forms'
            registration_url = reverse('users:detail', kwargs={'username': user.username})
            registration_tooltip = _(f'Complete requirements: {", ".join(missing_items)}')
        else:
            # Requirements met but enrollment closed
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
                'label': _('Notifications'),
                'url': reverse('users:notification_list'),
                'icon_class': 'bi bi-bell',
                'show_notification_badge': True,
            },
            {
                'label': _('Documents'),
                'url': reverse('users:document_list'),
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
                'label': _('Registration'),
                'url': registration_url,
                'icon_class': 'bi bi-grid-3x3-gap',
                'registration_status': registration_status,  # 'open', 'closed_forms', or 'closed_season'
                'registration_tooltip': registration_tooltip,
                'show_status_indicator': True,
            },
            {
                'label': _('Programs'),
                'url': reverse('portal:programs'),
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('My Attendance'),
                'url': reverse('portal:my_attendance'),
                'icon_class': 'bi bi-calendar-check',
            },
            {
                'label': _('Members'),
                'url': reverse('portal:all_members'),
                'icon_class': 'bi bi-people',
            },
            {
                'label': _('Volunteers'),
                'url': reverse('portal:all_volunteers'),
                'icon_class': 'bi bi-people-fill',
            },
            {
                'label': _('Tasks'),
                'url': '/surveys',
                'icon_class': 'bi bi-file-earmark-bar-graph',
            },
        ]
    
    # Manager navigation - Same as volunteer but with additional Manage Programs option
    elif role == 'manager':
        # Determine registration status for better UI feedback
        from inclusive_world_portal.portal.models import EnrollmentSettings
        
        enrollment_settings = EnrollmentSettings.get_settings()
        enrollment_open = enrollment_settings.enrollment_open
        meets_requirements, missing_items = user.enrollment_requirements_status
        
        # Managers can register if requirements are met and enrollment is open (no payment needed)
        can_register = meets_requirements and enrollment_open
        
        # Determine registration status and message
        if can_register:
            # Requirements met and enrollment open
            registration_status = 'open'
            registration_url = reverse('portal:volunteer_program_catalog')
            registration_tooltip = _('Registration is open')
        elif not meets_requirements:
            # Requirements not met
            registration_status = 'closed_forms'
            registration_url = reverse('users:detail', kwargs={'username': user.username})
            registration_tooltip = _(f'Complete requirements: {", ".join(missing_items)}')
        else:
            # Requirements met but enrollment closed
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
                'label': _('Notifications'),
                'url': reverse('users:notification_list'),
                'icon_class': 'bi bi-bell',
                'show_notification_badge': True,
            },
            {
                'label': _('Documents'),
                'url': reverse('users:document_list'),
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
                'label': _('Registration'),
                'url': registration_url,
                'icon_class': 'bi bi-grid-3x3-gap',
                'registration_status': registration_status,  # 'open', 'closed_forms', or 'closed_season'
                'registration_tooltip': registration_tooltip,
                'show_status_indicator': True,
            },
            {
                'label': _('Programs'),
                'url': reverse('portal:programs'),
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('My Attendance'),
                'url': reverse('portal:my_attendance'),
                'icon_class': 'bi bi-calendar-check',
            },
            {
                'label': _('Members'),
                'url': reverse('portal:all_members'),
                'icon_class': 'bi bi-people',
            },
            {
                'label': _('Volunteers'),
                'url': reverse('portal:all_volunteers'),
                'icon_class': 'bi bi-people-fill',
            },
            {
                'label': _('Enrollment Settings'),
                'url': reverse('portal:enrollment_settings'),
                'icon_class': 'bi bi-gear',
            },
            {
                'label': _('Tasks'),
                'url': '/surveys',
                'icon_class': 'bi bi-file-earmark-bar-graph',
            },
        ]
        return nav_items
    
    return common_items


def navigation_context(request):
    """
    Context processor to add navigation items to all templates.
    """
    nav_items = []
    role_display = None
    unread_notifications_count = 0
    
    if request.user.is_authenticated:
        nav_items = get_navigation_items(request.user)
        role_display = request.user.get_role_display()
        # Get unread notification count
        unread_notifications_count = request.user.notifications.unread().count()
    
    return {
        'nav_items': nav_items,
        'user_role_display': role_display,
        'unread_notifications_count': unread_notifications_count,
    }
