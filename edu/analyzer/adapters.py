from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user_email = sociallogin.user.email
        if not sociallogin.is_existing and user_email:
            try:
                email_address = EmailAddress.objects.get(email=user_email)
                if email_address.user:
                    sociallogin.connect(request, email_address.user)
                    raise ImmediateHttpResponse(HttpResponseRedirect('/'))
            except EmailAddress.DoesNotExist:
                pass
