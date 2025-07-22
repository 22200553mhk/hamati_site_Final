# analyzer/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('save-result/', views.save_result, name='save_result'),
    path('report/', views.generate_report, name='generate_report'),

    path('profile/', views.user_profile, name='user_profile'),
    path('save-exam/', views.save_exam_to_db, name='save_exam_to_db'),

    # مسیر جدید برای حذف حساب کاربری
    path('profile/delete/', views.delete_account, name='delete_account'),
# مسیر جدید برای صفحه فرود هوشمند
    path('account/redirect/', views.account_redirect, name='account_redirect'),
]