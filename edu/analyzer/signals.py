from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import random
import string

User = get_user_model()

def generate_unique_username(base):
    """ایجاد username منحصر به فرد"""
    while True:
        username = f"{base}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
        if not User.objects.filter(username=username).exists():
            return username

@receiver(pre_social_login)
def populate_user_fields(sender, request, sociallogin, **kwargs):
    user = sociallogin.user

    # فقط اگر username خالی یا 'user' بود، تغییرش بده
    if not user.username or user.username.lower() == 'user':
        full_name = sociallogin.account.extra_data.get('name', 'user')
        base_username = ''.join(e for e in full_name if e.isalnum())[:10] or 'user'
        user.username = generate_unique_username(base_username)

    # نام واقعی را از Google بگیر
    full_name = sociallogin.account.extra_data.get('name')
    if full_name:
        user.name = full_name
