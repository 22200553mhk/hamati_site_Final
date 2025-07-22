from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # sociallogin.user همان کاربری است که allauth از اطلاعات گوگل ساخته است
        email = sociallogin.user.email

        # اگر ایمیل وجود داشت
        if email:
            try:
                # چک می‌کنیم آیا کاربری با این ایمیل از قبل در دیتابیس ما وجود دارد یا نه
                user = User.objects.get(email=email)

                # اگر وجود داشت، این اکانت گوگل را به همان کاربر قدیمی متصل می‌کنیم
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                # اگر کاربری با این ایمیل وجود نداشت، روال عادی ثبت‌نام ادامه پیدا می‌کند
                pass