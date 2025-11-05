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
def get_volunteer_name(user):
    """
    Get the full name of a volunteer user.
    """
    if user:
        return user.name
    return "Unassigned"
