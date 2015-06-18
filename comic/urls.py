from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<comic_path>[\w]+)\/$', views.index, name='index'),
    url(r'^read\/(?P<comic_path>[\w]+)\/(?P<page>[0-9]+)\/$', views.read_comic, name='read_comic'),
    url(r'^read\/(?P<comic_path>[\w]+)\/(?P<page>[0-9]+)\/img$', views.get_image, name='get_image'),
    url(r"^file\/(?P<page>[0-9]+)\/(?P<file_name>[\w.\s'\(\)\-]+)\/$", views.read_comic, name='read_comic'),
    url(r"^file\/(?P<page>[0-9]+)\/(?P<file_name>[\w.\s'\(\)\-]+)\/img$", views.get_image, name='get_image'),
]