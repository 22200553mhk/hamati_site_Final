from allauth.account.models import EmailAddress

class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # این کد فقط برای کاربرانی که وارد شده‌اند اجرا می‌شود
        if request.user.is_authenticated:
            try:
                # آدرس ایمیل اصلی کاربر را پیدا می‌کنیم
                email_obj = EmailAddress.objects.get(user=request.user, primary=True)

                # اگر به هر دلیلی تایید نشده بود، آن را تایید می‌کنیم
                if not email_obj.verified:
                    email_obj.verified = True
                    email_obj.save()
            except EmailAddress.DoesNotExist:
                # اگر ایمیلی برای کاربر ثبت نشده بود، کاری انجام نمی‌دهیم
                pass

        response = self.get_response(request)
        return response