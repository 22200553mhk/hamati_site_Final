from django import template

register = template.Library()

@register.filter
def times(value):
    """Return a range up to the given integer value."""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return range(0)
