from django.shortcuts import render, redirect, RequestContext
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from comic_auth.forms import LoginForm


def comic_login(request):
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if request.GET.has_key('next'):
                        return redirect(request.GET['next'])
                    else:
                        return redirect('/comic/')
                else:
                    context = RequestContext(request, {
                        'error': True,

                    })
                    return render(request, 'comic_auth/login.html', context)
        else:
            context = RequestContext(request, {
                'error': True,
                'form': form
            })
            return render(request, 'comic_auth/login.html', context)
    else:
        if not User.objects.all().exists():
            return redirect('/setup/')
        form = LoginForm()
        context = RequestContext(request, {
            'form': form
        })
        return render(request, 'comic_auth/login.html', context)


def comic_logout(request):
    logout(request)
    return redirect('/login/')
