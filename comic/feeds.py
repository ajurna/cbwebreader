from django.contrib.auth.models import User
from django.contrib.syndication.views import Feed
from django.db.models import Case, When, PositiveSmallIntegerField, F, QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from comic.models import ComicBook, UserMisc, Directory


class RecentComicsAPI(Feed):
    title = "CBWebReader Recent Comics"
    link = "/read/"
    description = "Recently added Comics"
    user: User

    def get_object(self, request: HttpRequest, *args, **kwargs) -> UserMisc:
        user_misc = get_object_or_404(UserMisc, feed_id=kwargs["user_selector"])
        self.user = user_misc.user
        return user_misc.user

    def items(self) -> QuerySet[ComicBook]:
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
