# core/urls.py
from django.urls import path
from .views import about_us_view

app_name = 'core'

urlpatterns = [
    path('about-us/', about_us_view, name='about_us'),
]