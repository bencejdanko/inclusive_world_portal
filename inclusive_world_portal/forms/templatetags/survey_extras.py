"""Survey template tags and filters."""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key."""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def addstr(arg1, arg2):
    """Concatenate arg1 & arg2."""
    return str(arg1) + str(arg2)
