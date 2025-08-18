from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.text import slugify
from analyzer.models import CustomUser

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        # ابتدا کاربر استاندارد را می‌سازیم
        user = super().populate_user(request, sociallogin, data)

        # نام و نام خانوادگی واقعی از گوگل
        user.first_name = data.get("first_name", "")
        user.last_name = data.get("last_name", "")

        # تولید username منحصربه‌فرد
        base_username = slugify(f"{user.first_name}_{user.last_name}") or "user"
        username = base_username
        counter = 1

        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user.username = username

        return user
