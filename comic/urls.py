from django.urls import path

from . import feeds, views

urlpatterns = [
    path("", views.comic_list, name="index"),
    path("settings/users/", views.users_page, name="users"),
    path("settings/users/<int:user_id>/", views.user_config_page, name="user_details"),
    path("settings/users/add/", views.user_add_page, name="add_users"),
    path("account/", views.account_page, name="account"),
    path("read/<comic_selector>/", views.read_comic, name="read_comic"),
    path("read/<comic_selector>/thumb", views.comic_thumbnail, name="comic_thumbnail"),
    path("set_page/<comic_selector>/<int:page>/", views.set_read_page, name="set_read_page"),
    path("read/<comic_selector>/<int:page>/img", views.get_image, name="get_image"),
    path("read/<comic_selector>/pdf", views.get_pdf, name="get_pdf"),
    path("recent/", views.recent_comics, name="recent_comics"),
    path("recent/json/", views.recent_comics_json, name="recent_comics_json"),
    path("edit/", views.comic_edit, name="comic_edit"),
    path("feed/<user_selector>/", feeds.RecentComics()),
    path("<directory_selector>/", views.comic_list, name="comic_list"),
    path("<directory_selector>/thumb", views.directory_thumbnail, name="directory_thumbnail"),
    path("action/<operation>/<item_type>/<selector>/", views.perform_action, name="perform_action")
]
