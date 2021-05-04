from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import is_safe_url, url_has_allowed_host_and_scheme

from comic_auth.forms import LoginForm


def comic_login(request):
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if "next" in request.GET:
                        if url_has_allowed_host_and_scheme(request.GET["next"], allowed_hosts=None):
                            return redirect(request.GET["next"])
                        else:
                            return redirect("/comic/")
                    else:
                        return redirect("/comic/")
                else:
                    return render(request, "comic_auth/login.html", {"error": True})
            else:
                return render(request, "comic_auth/login.html", {"error": True, "form": form})
        else:
            return render(request, "comic_auth/login.html", {"error": True, "form": form})
    else:
        if not User.objects.all().exists():
            return redirect("/setup/")
        form = LoginForm()
        context = {"form": form}
        return render(request, "comic_auth/login.html", context)


def comic_logout(request):
    logout(request)
    return redirect("/login/")
