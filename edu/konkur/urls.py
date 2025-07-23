# konkur/urls.py

from allauth.account.views import LogoutView

from django.contrib import admin
from django.urls import path, include
from analyzer.views import CustomSignupView
from analyzer.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),

    # ما آدرس ثبت‌نام را بازنویسی می‌کنیم تا از ویو سفارشی ما استفاده کند
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),

    # و در نهایت آدرس‌های برنامه خودمان
    path('', include('analyzer.urls')),
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path("accounts/logout/", LogoutView.as_view(template_name="account/logout.html"), name="account_logout"),

    path('accounts/', include('allauth.urls')),

]