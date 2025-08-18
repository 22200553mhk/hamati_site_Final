# core/views.py
from django.shortcuts import render

def about_us_view(request):
    # این ویو فقط قالب HTML را رندر می‌کند
    return render(request, 'core/about_us.html')