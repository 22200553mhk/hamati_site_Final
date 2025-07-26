# analyzer/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('save-result/', views.save_result, name='save_result'),
    path('report/', views.generate_report, name='generate_report'),
    path('profile/', views.user_profile, name='user_profile'),
    path('save-exam/', views.save_exam_to_db, name='save_exam_to_db'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('account/redirect/', views.account_redirect, name='account_redirect'),
    path('profile/delete_exam/<int:exam_id>/', views.delete_single_exam, name='delete_single_exam'),
    path('profile/delete_all_exams/', views.delete_all_exams, name='delete_all_exams'),

]