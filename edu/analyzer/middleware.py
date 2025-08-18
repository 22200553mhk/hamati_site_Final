from django.shortcuts import redirect
from django.urls import reverse
from allauth.account.models import EmailAddress
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser



class EmailVerificationMiddleware:
    """
    جلوی دسترسی کاربرانی که ایمیل‌شان تایید نشده را می‌گیرد
    بدون اینکه دوباره ایمیل تایید بفرستد.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                email_address = EmailAddress.objects.get(user=request.user, email=request.user.email)
                if not email_address.verified and request.path != reverse('account_email_verification_sent'):
                    return redirect('account_email_verification_sent')
            except EmailAddress.DoesNotExist:
                pass
        return self.get_response(request)


