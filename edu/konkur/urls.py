# konkur/urls.py

from django.contrib import admin
from django.urls import path, include
from analyzer.views import CustomSignupView  # <-- ایمپورت ویو جدید

urlpatterns = [
    path('admin/', admin.site.urls),

    # ما آدرس ثبت‌نام را بازنویسی می‌کنیم تا از ویو سفارشی ما استفاده کند
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),

    # سپس بقیه آدرس‌های allauth را اضافه می‌کنیم
    path('accounts/', include('allauth.urls')),

    # و در نهایت آدرس‌های برنامه خودمان
    path('', include('analyzer.urls')),
]