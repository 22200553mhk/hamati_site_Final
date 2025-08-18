from django import forms
from django.core.validators import RegexValidator
from allauth.account.forms import SignupForm

username_validator = RegexValidator(
    r'^[a-zA-Z0-9\u0600-\u06FF\s]+$',
    'نام کاربری فقط می‌تواند شامل حروف، اعداد و فاصله باشد.'
)

class CustomSignupForm(SignupForm):
    username = forms.CharField(
        label='نام کاربری',
        max_length=150,
        validators=[username_validator],
        widget=forms.TextInput(attrs={'placeholder': 'نام کاربری خود را وارد کنید'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
