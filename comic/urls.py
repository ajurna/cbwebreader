from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.comic_list, name='index'),
    url(r'^settings/$', views.settings_page, name='settings'),
    url(r'^settings/users/$', views.users_page, name='users'),
    url(r'^settings/users/(?P<user_id>[0-9]+)/$', views.user_config_page, name='users'),
    url(r'^settings/users/add/$', views.user_add_page, name='users'),
    url(r'^account/$', views.account_page, name='account'),
    url(r'^read/(?P<comic_selector>[\w-]+)/(?P<page>[0-9]+)/$', views.read_comic, name='read_comic'),
    url(r'^read/(?P<comic_selector>[\w-]+)/(?P<page>[0-9]+)/img$', views.get_image, name='get_image'),
    url(r'^(?P<directory_selector>[\w-]+)/$', views.comic_list, name='comic_list'),
]
