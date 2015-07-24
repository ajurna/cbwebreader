from django import forms
from django.contrib.auth.models import User

from os import path

from comic.models import Setting


class InitialSetupForm(forms.Form):
    username = forms.CharField(help_text='Username',
                               widget=forms.TextInput(
                                   attrs={
                                       'class': 'form-control',
                                   }
                               ))
    email = forms.CharField(help_text='Email Address',
                            widget=forms.TextInput(
                                attrs={
                                    'class': 'form-control'
                                }
                            ))
    password = forms.CharField(help_text='New Password',
                               widget=forms.PasswordInput(
                                   attrs={
                                       'class': 'form-control',
                                   }
                               ))
    password_confirm = forms.CharField(help_text='New Password Confirmation',
                                       widget=forms.PasswordInput(
                                           attrs={
                                               'class': 'form-control',
                                           }
                                       ))
    base_dir = forms.CharField(help_text='Base Directory',
                               widget=forms.TextInput(
                                   attrs={
                                       'class': 'form-control'
                                   }
                               ))

    def clean_base_dir(self):
        data = self.cleaned_data['base_dir']
        if not path.isdir(data):
            raise forms.ValidationError('This is not a valid Directory')
        return data

    def clean(self):
        form_data = self.cleaned_data
        if form_data['password'] != form_data['password_confirm']:
            raise forms.ValidationError('Passwords do not match.')
        if len(form_data['password']) < 8:
            raise forms.ValidationError('Password is too short')
        return form_data


class AccountForm(forms.Form):
    username = forms.CharField(help_text='Username',
                               required=False,
                               widget=forms.TextInput(
                                   attrs={
                                       'class': 'form-control disabled',
                                       'readonly': True,
                                   }
                               ))
    email = forms.CharField(help_text='Email Address',
                            widget=forms.TextInput(
                                attrs={
                                    'class': 'form-control'
                                }
                            ))
    password = forms.CharField(help_text='New Password',
                               required=False,
                               widget=forms.PasswordInput(
                                   attrs={
                                       'class': 'form-control',
                                   }
                               ))
    password_confirm = forms.CharField(help_text='New Password Confirmation',
                                       required=False,
                                       widget=forms.PasswordInput(
                                           attrs={
                                               'class': 'form-control',
                                           }
                                       ))

    def clean_email(self):
        data = self.cleaned_data['email']
        user = User.objects.get(username=self.cleaned_data['username'])
        if data == user.email:
            return data
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError('Email Address is in use')
        return data

    def clean(self):
        form_data = self.cleaned_data
        if form_data['password'] != form_data['password_confirm']:
            raise forms.ValidationError('Passwords do not match.')
        if len(form_data['password']) < 8 & len(form_data['password']) != 0:
            raise forms.ValidationError('Password is too short')
        return form_data


class AddUserForm(forms.Form):
    username = forms.CharField(help_text='Username',
                               widget=forms.TextInput(
                                   attrs={
                                       'class': 'form-control',
                                   }
                               ))
    email = forms.CharField(help_text='Email Address',
                            widget=forms.TextInput(
                                attrs={
                                    'class': 'form-control'
                                }
                            ))
    password = forms.CharField(help_text='New Password',
                               widget=forms.PasswordInput(
                                   attrs={
                                       'class': 'form-control',
                                   }
                               ))
    password_confirm = forms.CharField(help_text='New Password Confirmation',
                                       widget=forms.PasswordInput(
                                           attrs={
                                               'class': 'form-control',
                                           }
                                       ))

    def clean_username(self):
        data = self.cleaned_data['username']
        if User.objects.filter(username=data).exists():
            raise forms.ValidationError('This username Exists.')
        return data

    def clean_email(self):
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError('Email Address is in use')
        return data

    def clean(self):
        form_data = self.cleaned_data
        if form_data['password'] != form_data['password_confirm']:
            raise forms.ValidationError('Passwords do not match.')
        if len(form_data['password']) < 8:
            raise forms.ValidationError('Password is too short')
        return form_data


class EditUserForm(forms.Form):
    username = forms.CharField(help_text='Username',
                               required=False,
                               widget=forms.TextInput(
                                   attrs={
                                       'class': 'form-control disabled',
                                       'readonly': True,
                                   }
                               ))
    email = forms.CharField(help_text='Email Address',
                            widget=forms.TextInput(
                                attrs={
                                    'class': 'form-control'
                                }
                            ))
    password = forms.CharField(help_text='New Password',
                               required=False,
                               widget=forms.PasswordInput(
                                   attrs={
                                       'class': 'form-control',
                                   }
                               ))
    # TODO: allow setting superuser on users

    @staticmethod
    def get_initial_values(user):
        out = {
            'username': user.username,
            'email': user.email
        }
        return out

    def clean_email(self):
        data = self.cleaned_data['email']
        user = User.objects.get(username=self.cleaned_data['username'])
        if data == user.email:
            return data
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError('Email Address is in use')
        return data

    def clean_password(self):
        data = self.cleaned_data['password']
        if len(data) < 8 & len(data) != 0:
            raise forms.ValidationError('Password is too short')
        return data


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

    def clean_base_dir(self):
        data = self.cleaned_data['base_dir']
        if not path.isdir(data):
            raise forms.ValidationError('This is not a valid Directory')
        return data

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
