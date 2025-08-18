# konkur/urls.py

from allauth.account.views import LogoutView
from analyzer import views
from django.conf import settings
from django.conf.urls.static import static
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
    path("accounts/delete/", views.delete_account, name="delete_account"),

    path('accounts/', include('allauth.urls')),
    path('accounts/cancel-signup/', views.delete_unverified_user, name='delete_unverified_user'),

    path("check_email_password/", views.check_email_exists_password, name="check_email_password"),

    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('articles/', include('blog.urls',namespace='articles')),
    path('', include('core.urls')),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

