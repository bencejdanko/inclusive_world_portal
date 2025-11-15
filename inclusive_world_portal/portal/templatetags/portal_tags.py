"""
Custom template tags and filters for the portal app.
"""
from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """
    Template filter to look up a value in a dictionary by key.
    Usage: {{ my_dict|lookup:my_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary by key.
    Alias for lookup filter for better readability.
    Usage: {{ my_dict|get_item:my_key }}
    Returns an empty list if the key is not found and we're iterating over it.
    """
    if dictionary is None:
        return []
    result = dictionary.get(key)
    # If result is None, return empty list for iteration safety
    return result if result is not None else []


@register.filter
def get_volunteer_name(user):
    """
    Get the full name of a volunteer user.
    """
    if user:
        return user.name
    return "Unassigned"


@register.filter
def buddy_lookup(buddy_map, enrollment):
    """
    Look up buddy for a specific enrollment (program + member combination).
    Usage: {{ buddy_map|buddy_lookup:enrollment }}
    Returns the volunteer_id if found, None otherwise.
    """
    if not buddy_map or not enrollment:
        return None
    # Create tuple key: (program_id_str, member_user_id)
    key = (str(enrollment.program.program_id), enrollment.user.id)
    return buddy_map.get(key)


@register.simple_tag
def get_buddy_for_member(buddy_map, program_id, member_id):
    """
    Look up buddy for a specific program and member combination.
    Usage: {% get_buddy_for_member buddy_map program_id member_id %}
    Returns the volunteer_id if found, None otherwise.
    """
    if not buddy_map:
        return None
    # Create tuple key: (program_id_str, member_user_id)
    key = (str(program_id), member_id)
    return buddy_map.get(key)
