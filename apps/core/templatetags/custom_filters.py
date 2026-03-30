from django import template

register = template.Library()


@register.filter
def replace(value, args):
    """
    Replace occurrences of a substring within a string.
    Usage: {{ value|replace:"old: new" }}
    Splits on ': ' (colon-space) to separate old and new values.
    """
    try:
        old, new = args.split(": ", 1)
        return str(value).replace(old, new)
    except (ValueError, AttributeError):
        return value
