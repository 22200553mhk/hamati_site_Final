from django import template
import jdatetime

register = template.Library()

@register.filter
def jalali_date(value, date_format="%Y/%m/%d"):
    if not value:
        return ""
    try:
        # تبدیل datetime میلادی به شمسی
        jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
        return jalali_date.strftime(date_format)
    except Exception:
        return value
