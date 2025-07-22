from allauth.account.decorators import verified_email_required
from django.contrib import messages
from django.shortcuts import redirect

def email_verified_required_custom(function):
    def wrap(request, *args, **kwargs):
        # از نگهبان آماده allauth استفاده می‌کنیم
        actual_decorator = verified_email_required(function)

        # اگر کاربر ایمیلش را تایید نکرده باشد
        if not request.user.emailaddress_set.filter(verified=True).exists():
            # یک پیام راهنما به او نمایش می‌دهیم
            messages.warning(request, 'برای دسترسی به این صفحه، لطفاً ابتدا ایمیل خود را تایید کنید. ایمیل فعال‌سازی برای شما ارسال شده است.')
            # و او را به صفحه اصلی هدایت می‌کنیم
            return redirect('dashboard')

        return actual_decorator(request, *args, **kwargs)

    return wrap