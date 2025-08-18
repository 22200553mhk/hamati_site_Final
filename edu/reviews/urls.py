# reviews/urls.py
from django.urls import path
from . import views

app_name = "reviews"
urlpatterns = [
    path('', views.review_page, name='review_page'),
    path("delete/<int:review_id>/", views.delete_review, name="delete_review"),
    # ✅ اینجا اشتباه تایپی اصلاح شد
    path('delete/all/', views.delete_all_reviews, name="delete_all_reviews"),
]