from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.comic_list, name='index'),
    url(r'^settings/$', views.settings_page, name='settings'),
    url(r'^account/$', views.account_page, name='account'),
    url(r'^(?P<comic_path>[\w]+)/$', views.comic_list, name='comic_list'),
    url(r'^read/(?P<comic_path>[\w]+)/(?P<page>[0-9]+)/$', views.read_comic, name='read_comic'),
    url(r'^read/(?P<comic_path>[\w]+)/(?P<page>[0-9]+)/img$', views.get_image, name='get_image'),
]
