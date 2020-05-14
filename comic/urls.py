from django.conf.urls import url

from . import feeds, views

urlpatterns = [
    url(r"^$", views.comic_list, name="index"),
    url(r"^settings/$", views.settings_page, name="settings"),
    url(r"^settings/users/$", views.users_page, name="users"),
    url(r"^settings/users/(?P<user_id>[0-9]+)/$", views.user_config_page, name="user_details"),
    url(r"^settings/users/add/$", views.user_add_page, name="add_users"),
    url(r"^account/$", views.account_page, name="account"),
    url(r"^read/(?P<comic_selector>[\w-]+)/(?P<page>[0-9]+)/$", views.read_comic, name="read_comic"),
    url(r"^read/(?P<comic_selector>[\w-]+)/(?P<page>[0-9]+)/img$", views.get_image, name="get_image"),
    url(r"^list_json/$", views.comic_list_json, name="comic_list_json1"),
    url(r"^list_json/(?P<directory_selector>[\w-]+)/$", views.comic_list_json, name="comic_list_json2"),
    url(r"^recent/$", views.recent_comics, name="recent_comics"),
    url(r"^recent/json/$", views.recent_comics_json, name="recent_comics_json"),
    url(r"^edit/$", views.comic_edit, name="comic_edit"),
    url(r"^feed/(?P<user_selector>[\w-]+)/$", feeds.RecentComics()),
    url(r"^(?P<directory_selector>[\w-]+)/$", views.comic_list, name="comic_list"),
]
