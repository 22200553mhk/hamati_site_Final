# analyzer/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # مسیرهای قبلی و جدید
    path('', views.dashboard, name='dashboard'),
    path('save-result/', views.save_result, name='save_result'),
    path('report/', views.generate_report, name='generate_report'),

    # مسیرهای جدید فقط برای کاربران لاگین کرده
    path('profile/', views.user_profile, name='user_profile'),
    path('save-exam/', views.save_exam_to_db, name='save_exam_to_db'),
]