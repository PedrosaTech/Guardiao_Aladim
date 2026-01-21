"""
Template tags customizados para orçamentos.
"""
from django import template

register = template.Library()


@register.filter
def dividir(value, arg):
    """
    Divide value por arg.
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

