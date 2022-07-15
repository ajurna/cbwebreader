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
from django.urls import path, re_path
from rest_framework import routers, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_extensions.routers import ExtendedDefaultRouter

from django.views.generic import TemplateView

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="CBWebReader API",
      default_version='v1',
      description="API to access your comic collection",
      contact=openapi.Contact(name="Ajurna", url="https://github.com/ajurna/cbwebreader"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny, ),
)


import comic.views
import comic_auth.views
from comic import rest

router = ExtendedDefaultRouter()
router.register(r'users', rest.UserViewSet)
router.register(r'groups', rest.GroupViewSet)
router.register(r'directory', rest.DirectoryViewSet)
router.register(r'comicbook', rest.ComicBookViewSet)
router.register(r'browse', rest.BrowseViewSet, basename='browse')
router.register(r'breadcrumbs', rest.BreadcrumbViewSet, basename='breadcrumbs')
router.register(r'generate_thumbnail', rest.GenerateThumbnailViewSet, basename='generate_thumbnail')
router.register(r'read', rest.ReadViewSet, basename='read')\
    .register('image', rest.ImageViewSet, basename='image', parents_query_lookups=['selector'])
router.register(r'set_read', rest.SetReadViewSet, basename='set_read')


urlpatterns = [
    # url(r"^$", comic.views.comic_redirect),
    # url(r"^login/", comic_auth.views.comic_login),
    # url(r"^logout/", comic_auth.views.comic_logout),
    # url(r"^setup/", comic.views.initial_setup),
    # url(r"^comic/", include("comic.urls")),
    path('admin/', admin.site.urls),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # path('image/<selector>/<int:page>', comic.views.get_image_api , name='get_image_api'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
    path("",
         TemplateView.as_view(template_name="application.html"),
         name="app",
         ),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
