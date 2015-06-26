from django import forms
from comic.models import Setting


class SettingsForm(forms.Form):
    base_dir = forms.CharField(help_text='Base Directory',
                               widget=forms.TextInput(
                                   attrs={
                                       'class': 'form-control'
                                   }
                               ))
    recaptcha = forms.BooleanField(help_text='Use Recaptcha',
                                   required=False,
                                   widget=forms.CheckboxInput(
                                       attrs={
                                           'class': 'checkbox'
                                       }
                                   ))
    recaptcha_public_key = forms.CharField(help_text='Recaptcha Public Key',
                                           required=False,
                                           widget=forms.TextInput(
                                               attrs={
                                                   'class': 'form-control'
                                               }
                                           ))
    recaptcha_private_key = forms.CharField(help_text='Recaptcha Private Key',
                                            required=False,
                                            widget=forms.TextInput(
                                                attrs={
                                                    'class': 'form-control'
                                                }
                                            ))

    @staticmethod
    def get_initial_values():
        base_dir, created = Setting.objects.get_or_create(name='BASE_DIR')
        recaptcha_public_key, created = Setting.objects.get_or_create(name='RECAPTCHA_PUBLIC_KEY')
        recaptcha_private_key, created = Setting.objects.get_or_create(name='RECAPTCHA_PRIVATE_KEY')
        recaptcha, created = Setting.objects.get_or_create(name='RECAPTCHA')
        if recaptcha.value == '1':
            recaptcha = True
        else:
            recaptcha = False
        initial = {
            'base_dir': base_dir.value,
            'recaptcha': recaptcha,
            'recaptcha_public_key': recaptcha_public_key.value,
            'recaptcha_private_key': recaptcha_private_key.value,
        }
        return initial
