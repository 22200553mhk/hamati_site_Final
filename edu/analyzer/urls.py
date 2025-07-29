from django.urls import path
from . import views

urlpatterns = [
    # صفحه اصلی جدید
    path('', views.home_view, name='home'),

    # صفحه ورود اطلاعات آزمون (داشبورد قبلی)
    path('dashboard/', views.dashboard, name='dashboard'),

    # سایر آدرس‌های شما بدون تغییر
    path('save-result/', views.save_result, name='save_result'),
    path('report/', views.generate_report, name='generate_report'),
    path('profile/', views.user_profile, name='user_profile'),
    path('save-exam/', views.save_exam_to_db, name='save_exam_to_db'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('profile/delete_exam/<int:exam_id>/', views.delete_single_exam, name='delete_single_exam'),
    path('profile/delete_all_exams/', views.delete_all_exams, name='delete_all_exams'),
    path('account/redirect/', views.account_redirect, name='account_redirect'),
]