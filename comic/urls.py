from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r"^file\/(?P<page>[0-9]+)\/(?P<file_name>[\w.\s'\(\)\-]+)\/$", views.read_comic, name='read_comic'),
    url(r"^file\/(?P<page>[0-9]+)\/(?P<file_name>[\w.\s'\(\)\-]+)\/img$", views.get_image, name='get_image'),
]