import uuid

from django.contrib.syndication.views import Feed
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import ComicBook, UserMisc


class RecentComics(Feed):
    title = "CBWebReader Recent Comics"
    link = "/comics/"
    description = "Recently added Comics"

    def get_object(self, request: HttpRequest, user_selector: str, *args, **kwargs) -> UserMisc:
        user_selector = uuid.UUID(bytes=urlsafe_base64_decode(user_selector))
        return get_object_or_404(UserMisc, feed_id=user_selector)

    @staticmethod
    def items() -> ComicBook:
        return ComicBook.objects.order_by('-date_added')[:10]

    def item_title(self, item: ComicBook) -> str:
        return item.file_name

    def item_description(self, item: ComicBook) -> str:
        return item.date_added.strftime('%a, %e %b %Y %H:%M')

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item: ComicBook) -> str:
        return '/comic/read/{0}/0/'.format(urlsafe_base64_encode(item.selector.bytes))
