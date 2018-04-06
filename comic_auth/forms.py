from django import forms
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget

from comic.models import Setting


class LoginForm(forms.Form):

    username = forms.CharField(max_length=50,
                               label='',
                               widget=forms.TextInput(
                                   attrs={
                                       'class': 'form-control',
                                       'placeholder': 'Username',
                                       'autofocus': True,
                                       'required': True,
                                   }
                               ))
    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput(
                                   attrs={
                                       'class': 'form-control',
                                       'placeholder': 'Username',
                                       'required': True,
                                   }
                               ))

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        setting, created = Setting.objects.get_or_create(name='RECAPTCHA')
        if created:
            setting.value = '0'
        if setting.value == '1':
            # public_key = Setting.objects.get(name='RECAPTCHA_PUBLIC_KEY').value
            # private_key = Setting.objects.get(name='RECAPTCHA_PRIVATE_KEY').value
            #
            # captcha = ReCaptchaField(
            #     public_key=public_key,
            #     private_key=private_key,
            # )
            self.fields['captcha'] = ReCaptchaField(widget=ReCaptchaWidget())
