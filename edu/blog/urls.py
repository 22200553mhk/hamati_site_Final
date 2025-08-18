from django.urls import path
from .views import category_list_view, article_detail_view



app_name = "articles"

urlpatterns = [
    path('categories/', category_list_view, name='category_list'),
    # می‌توانید یک URL هم برای نمایش هر مقاله تعریف کنید (فعلا لازم نیست)
    path('article/<str:slug>/', article_detail_view, name='article_detail'),

]