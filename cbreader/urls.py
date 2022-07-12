"""cbreader URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

import comic.views
import comic_auth.views
from comic import rest

router = routers.DefaultRouter()
router.register(r'users', rest.UserViewSet)
router.register(r'groups', rest.GroupViewSet)
router.register(r'directory', rest.DirectoryViewSet)
router.register(r'comicbook', rest.ComicBookViewSet)
router.register(r'browse', rest.BrowseViewSet, basename='browse')
router.register(r'breadcrumbs', rest.BreadcrumbViewSet, basename='breadcrumbs')

urlpatterns = [
    url(r"^$", comic.views.comic_redirect),
    url(r"^login/", comic_auth.views.comic_login),
    url(r"^logout/", comic_auth.views.comic_logout),
    url(r"^setup/", comic.views.initial_setup),
    url(r"^comic/", include("comic.urls")),
    url(r"^admin/", admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
