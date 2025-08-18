from django import template

register = template.Library()

@register.filter
def times(number):
    try:
        number = int(number)  # تبدیل به عدد صحیح
        return range(number)
    except (ValueError, TypeError):
        return range(0)
