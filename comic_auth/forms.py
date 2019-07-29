from django import forms
from django.conf import settings
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget


class LoginForm(forms.Form):

    username = forms.CharField(
        max_length=50,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username", "autofocus": True, "required": True}
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password", "required": True}),
    )

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        if settings.CBREADER_USE_RECAPTCHA if hasattr(settings, "CBREADER_USE_RECAPTCHA") else False:
            self.fields["captcha"] = ReCaptchaField(widget=ReCaptchaWidget())
