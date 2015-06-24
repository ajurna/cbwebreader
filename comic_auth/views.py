from django.shortcuts import render, redirect, RequestContext
from django.contrib.auth import authenticate, login, logout


def comic_login(request):
    if request.POST:
        user = authenticate(username=request.POST['user'],
                            password=request.POST['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                if request.GET.has_key('next'):
                    return redirect(request.GET['next'])
                else:
                    return redirect('/comic/')
            else:
                context = RequestContext(request, {
                    'error': True
                })
                return render(request, 'comic_auth/login.html', context)
    else:
        context = RequestContext(request, {})
        return render(request, 'comic_auth/login.html', context)

def comic_logout(request):
    logout(request)
    return redirect('/login/')