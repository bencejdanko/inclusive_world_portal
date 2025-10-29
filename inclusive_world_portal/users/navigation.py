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
        return [
            {
                'label': _('Dashboard'),
                'url': reverse('users:member_dashboard'),
                'icon_class': 'bi bi-house-door',
            },
            {
                'label': _('One Page Description'),
                'url': reverse('users:opd_editor'),
                'icon_class': 'bi bi-file-earmark-text',
            },
            {
                'label': _('Profile & Registration'),
                'url': reverse('users:update'),
                'icon_class': 'bi bi-pencil-square',
            },
            {
                'label': _('Fees'),
                'url': '#',  # TODO: Add URL when view is created
                'icon_class': 'bi bi-tag',
            },
            {
                'label': _('My Programs'),
                'url': '#',  # TODO: Add URL when view is created
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('My Attendance'),
                'url': '#',  # TODO: Add URL when view is created
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('My Surveys'),
                'url': reverse('users:survey_start'),
                'icon_class': 'bi bi-file-text',
            },
        ]
    
    # Volunteer navigation
    elif role == 'volunteer':
        return [
            {
                'label': _('Dashboard'),
                'url': reverse('home'),
                'icon_class': 'bi bi-house-door',
            },
            {
                'label': _('My Schedule'),
                'url': '#',
                'icon_class': 'bi bi-calendar',
            },
            {
                'label': _('Members'),
                'url': '#',
                'icon_class': 'bi bi-people',
            },
            {
                'label': _('Training'),
                'url': '#',
                'icon_class': 'bi bi-book',
            },
            {
                'label': _('Profile'),
                'url': reverse('users:update'),
                'icon_class': 'bi bi-person',
            },
        ]
    
    # Person Centered Manager navigation
    elif role == 'person_centered_manager':
        return [
            {
                'label': _('Dashboard'),
                'url': reverse('home'),
                'icon_class': 'bi bi-house-door',
            },
            {
                'label': _('My Caseload'),
                'url': '#',
                'icon_class': 'bi bi-people',
            },
            {
                'label': _('Programs'),
                'url': '#',
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('Reports'),
                'url': '#',
                'icon_class': 'bi bi-file-earmark-bar-graph',
            },
            {
                'label': _('Resources'),
                'url': '#',
                'icon_class': 'bi bi-folder',
            },
            {
                'label': _('Profile'),
                'url': reverse('users:update'),
                'icon_class': 'bi bi-person',
            },
        ]
    
    # Manager navigation
    elif role == 'manager':
        return [
            {
                'label': _('Dashboard'),
                'url': reverse('home'),
                'icon_class': 'bi bi-house-door',
            },
            {
                'label': _('All Members'),
                'url': '#',
                'icon_class': 'bi bi-people',
            },
            {
                'label': _('Staff'),
                'url': '#',
                'icon_class': 'bi bi-person-badge',
            },
            {
                'label': _('Programs'),
                'url': '#',
                'icon_class': 'bi bi-layers',
            },
            {
                'label': _('Financials'),
                'url': '#',
                'icon_class': 'bi bi-cash-stack',
            },
            {
                'label': _('Reports'),
                'url': '#',
                'icon_class': 'bi bi-file-earmark-bar-graph',
            },
            {
                'label': _('Settings'),
                'url': '#',
                'icon_class': 'bi bi-gear',
            },
        ]
    
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
