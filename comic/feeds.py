import uuid

from django.contrib.auth.models import User
from django.contrib.syndication.views import Feed
from django.db.models import Case, When, PositiveSmallIntegerField, F
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import ComicBook, UserMisc, Directory


class RecentComics(Feed):
    title = "CBWebReader Recent Comics"
    link = "/comics/"
    description = "Recently added Comics"
    user: User

    def get_object(self, request: HttpRequest, user_selector: str, *args, **kwargs) -> UserMisc:
        user_selector = uuid.UUID(bytes=urlsafe_base64_decode(user_selector))
        user_misc = get_object_or_404(UserMisc, feed_id=user_selector)
        self.user = user_misc.user
        return user_misc.user

    def items(self) -> ComicBook:
        comics = ComicBook.objects.order_by("-date_added")
        comics = comics.annotate(
            classification=Case(
                When(directory__isnull=True, then=Directory.Classification.C_18),
                default=F('directory__classification'),
                output_field=PositiveSmallIntegerField(choices=Directory.Classification.choices)
            )
        )
        comics = comics.filter(classification__lte=self.user.usermisc.allowed_to_read)
        return comics[:10]

    def item_title(self, item: ComicBook) -> str:
        return item.file_name

    def item_description(self, item: ComicBook) -> str:
        return item.date_added.strftime("%a, %e %b %Y %H:%M")

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item: ComicBook) -> str:
        return reverse('read_comic', args=(urlsafe_base64_encode(item.selector.bytes),))


class RecentComicsAPI(Feed):
    title = "CBWebReader Recent Comics"
    link = "/read/"
    description = "Recently added Comics"
    user: User

    def get_object(self, request: HttpRequest, user_selector: str, *args, **kwargs) -> UserMisc:
        user_misc = get_object_or_404(UserMisc, feed_id=user_selector)
        self.user = user_misc.user
        return user_misc.user

    def items(self) -> ComicBook:
        comics = ComicBook.objects.order_by("-date_added")
        comics = comics.annotate(
            classification=Case(
                When(directory__isnull=True, then=Directory.Classification.C_18),
                default=F('directory__classification'),
                output_field=PositiveSmallIntegerField(choices=Directory.Classification.choices)
            )
        )
        comics = comics.filter(classification__lte=self.user.usermisc.allowed_to_read)
        return comics[:10]

    def item_title(self, item: ComicBook) -> str:
        return item.file_name

    def item_description(self, item: ComicBook) -> str:
        return item.date_added.strftime("%a, %e %b %Y %H:%M")

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item: ComicBook) -> str:
        return f'#/read/{item.selector}/'
