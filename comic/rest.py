from itertools import chain
from uuid import UUID

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db.models import Count, Case, When, F, PositiveSmallIntegerField, Max, Q
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, serializers, mixins, permissions, status, renderers
from rest_framework.decorators import api_view, action
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from comic import models
from comic.util import generate_directory, generate_breadcrumbs_from_path, DirFile
from pathlib import Path


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class DirectorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Directory

        fields = ['name', 'parent', 'selector', 'thumbnail', 'thumbnail_issue', 'thumbnail_index', 'classification']


class DirectoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):
    """
    API endpoint that allows Directories to be viewed.
    """
    queryset = models.Directory.objects.all()
    lookup_field = 'selector'
    serializer_class = DirectorySerializer
    permission_classes = [permissions.IsAuthenticated]


class ComicBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ComicBook
        fields = ['file_name', 'date_added', 'directory', 'selector', 'version', 'thumbnail', 'thumbnail_index']


class ComicBookViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = models.ComicBook.objects.all()
    serializer_class = ComicBookSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['directory', 'selector']


class BrowseSerializer(serializers.Serializer):
    selector = serializers.UUIDField()
    title = serializers.CharField()
    progress = serializers.IntegerField()
    total = serializers.IntegerField()
    type = serializers.CharField()
    thumbnail = serializers.FileField()
    classification = serializers.IntegerField()



class BrowseViewSet(viewsets.ViewSet):
    serializer_class = BrowseSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'selector'

    def list(self, request):
        queryset = []
        serializer = self.serializer_class(self.generate_directory(request.user), many=True)
        return Response(serializer.data)

    def retrieve(self, request, selector: UUID):
        queryset = []
        directory = models.Directory.objects.get(selector=selector)
        serializer = self.serializer_class(self.generate_directory(request.user, directory), many=True)
        return Response(serializer.data)

    @staticmethod
    def clean_directories(directories, dir_path, directory=None):

        dir_db_set = set([Path(settings.COMIC_BOOK_VOLUME, x.path) for x in directories])
        dir_list = set([x for x in sorted(dir_path.glob('*')) if x.is_dir()])
        # Create new directories db instances
        for new_directory in dir_list - dir_db_set:
            models.Directory(name=new_directory.name, parent=directory).save()

        # Remove stale db instances
        for stale_directory in dir_db_set - dir_list:
            models.Directory.objects.get(name=stale_directory.name, parent=directory).delete()

    @staticmethod
    def clean_files(files, user, dir_path, directory=None):
        file_list = set([x for x in sorted(dir_path.glob('*')) if x.is_file()])
        files_db_set = set([Path(dir_path, x.file_name) for x in files])

        # Parse new comics
        for new_comic in file_list - files_db_set:
            if new_comic.suffix.lower() in [".rar", ".zip", ".cbr", ".cbz", ".pdf"]:
                book = models.ComicBook.process_comic_book(new_comic, directory)
                models.ComicStatus(user=user, comic=book).save()

        # Remove stale comic instances
        for stale_comic in files_db_set - file_list:
            models.ComicBook.objects.get(file_name=stale_comic.name, directory=directory).delete()

    def generate_directory(self, user: User, directory=None):
        """
        :type user: User
        :type directory: Directory
        """
        dir_path = Path(settings.COMIC_BOOK_VOLUME, directory.path) if directory else settings.COMIC_BOOK_VOLUME
        files = []

        dir_db_query = models.Directory.objects.filter(parent=directory)
        self.clean_directories(dir_db_query, dir_path, directory)

        file_db_query = models.ComicBook.objects.filter(directory=directory)
        self.clean_files(file_db_query, user, dir_path, directory)

        dir_db_query = dir_db_query.annotate(
            total=Count('comicbook', distinct=True),
            progress=Count('comicbook__comicstatus', Q(comicbook__comicstatus__finished=True,
                                                       comicbook__comicstatus__user=user), distinct=True)
        )
        files.extend(dir_db_query)

        # Create Missing Status
        new_status = [models.ComicStatus(comic=file, user=user) for file in
                      file_db_query.exclude(comicstatus__in=models.ComicStatus.objects.filter(
                          comic__in=file_db_query, user=user))]
        models.ComicStatus.objects.bulk_create(new_status)

        file_db_query = file_db_query.annotate(
            total=Count('comicpage', distinct=True),
            progress=F('comicstatus__last_read_page'),
            finished=F('comicstatus__finished'),
            unread=F('comicstatus__unread'),
            user=F('comicstatus__user'),
            classification=Case(
                When(directory__isnull=True, then=models.Directory.Classification.C_18),
                default=F('directory__classification'),
                output_field=PositiveSmallIntegerField(choices=models.Directory.Classification.choices)
            )
        ).filter(Q(user__isnull=True) | Q(user=user.id))

        files.extend(file_db_query)

        # files = [file for file in files if file.classification <= user.usermisc.allowed_to_read]

        comics_to_annotate = []

        for file in chain(file_db_query, dir_db_query):
            if file.thumbnail and not Path(file.thumbnail.path).exists():
                file.thumbnail.delete()
                file.save()
        files.sort(key=lambda x: x.title)
        files.sort(key=lambda x: x.type, reverse=True)
        return files


class BreadcrumbSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    selector = serializers.UUIDField()
    name = serializers.CharField()


class BreadcrumbViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BreadcrumbSerializer
    lookup_field = 'selector'

    def retrieve(self, request, selector: UUID):
        queryset = []
        comic = False
        try:
            directory = models.Directory.objects.get(selector=selector)
        except models.Directory.DoesNotExist:
            comic = models.ComicBook.objects.get(selector=selector)
            directory = comic.directory

        for index, item in enumerate(generate_breadcrumbs_from_path(directory, comic)):
            queryset.append({
                "id": index,
                "selector": item.selector,
                "name": item.name,
            })
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class GenerateThumbnailSerializer(serializers.Serializer):
    selector = serializers.UUIDField()
    thumbnail = serializers.FileField()


class GenerateThumbnailViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GenerateThumbnailSerializer
    lookup_field = 'selector'

    def retrieve(self, request, selector: UUID):
        try:
            directory = models.Directory.objects.get(selector=selector)
            if not directory.thumbnail:
                directory.generate_thumbnail()
            return Response(
                self.serializer_class({
                    "selector": directory.selector,
                    "thumbnail": directory.thumbnail
                }).data
            )
        except models.Directory.DoesNotExist:
            comic = models.ComicBook.objects.get(selector=selector)
            if not comic.thumbnail:
                comic.generate_thumbnail()
            return Response(
                self.serializer_class({
                    "selector": comic.selector,
                    "thumbnail": comic.thumbnail
                }).data
            )


class PageSerializer(serializers.Serializer):
    index = serializers.IntegerField()
    page_file_name = serializers.CharField()
    content_type = serializers.CharField()


class ReadSerializer(serializers.Serializer):
    selector = serializers.UUIDField()
    title = serializers.CharField()
    last_read_page = serializers.IntegerField()
    pages = PageSerializer(many=True)


class ReadViewSet(viewsets.ViewSet):
    serializer_class = ReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'selector'

    def retrieve(self, request, selector: UUID):
        comic = get_object_or_404(models.ComicBook, selector=selector)
        misc, _ = models.UserMisc.objects.get_or_create(user=request.user)
        pages = models.ComicPage.objects.filter(Comic=comic)
        status, _ = models.ComicStatus.objects.get_or_create(comic=comic, user=request.user)
        data = {
            "selector": comic.selector,
            "title": comic.file_name,
            "last_read_page": status.last_read_page,
            "pages": pages,
        }
        serializer = self.serializer_class(data)
        return Response(serializer.data)


class ReadPageSerializer(serializers.Serializer):
    page = serializers.IntegerField()


class SetReadViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReadPageSerializer
    lookup_field = 'selector'

    @swagger_auto_schema(operation_description="PUT /set_read/{selector}/", request_body=ReadPageSerializer)
    def update(self, request, selector):
        serializer = ReadPageSerializer(data=request.data)

        if serializer.is_valid():
            comic_status, _ = models.ComicStatus.objects.get_or_create(comic_id=selector, user=request.user)
            comic_status.last_read_page = serializer.data['page']
            comic_status.unread = False
            if models.ComicPage.objects.filter(Comic=comic_status.comic).aggregate(Max("index"))["index__max"] \
                    == comic_status.last_read_page:
                comic_status.finished = True
            else:
                comic_status.finished = False

            comic_status.save()
            return Response({'status': 'page set'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class PassthroughRenderer(renderers.BaseRenderer):
    """
        Return data as-is. View should supply a Response.
    """
    media_type = '*/*'
    format = ''

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class ImageViewSet(viewsets.ViewSet):
    queryset = models.ComicPage.objects.all()
    lookup_field = 'page'
    renderer_classes = [PassthroughRenderer]

    def retrieve(self, request, parent_lookup_selector, page):
        book = models.ComicBook.objects.get(selector=parent_lookup_selector)
        img, content = book.get_image(int(page))
        self.renderer_classes[0].media_type = content
        response = FileResponse(img, content_type=content)
        return response


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class RecentComicsSerializer(serializers.ModelSerializer):
    total_pages = serializers.IntegerField()
    unread = serializers.BooleanField()
    finished = serializers.BooleanField()
    last_read_page = serializers.IntegerField()

    class Meta:
        model = models.ComicBook
        fields = ['file_name', 'date_added', 'selector', 'total_pages', 'unread', 'finished', 'last_read_page']


class RecentComicsView(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = models.ComicBook.objects.all()
    serializer_class = RecentComicsSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if "search_text" in self.request.query_params:
            query = models.ComicBook.objects.filter(file_name__icontains=self.request.query_params["search_text"])
        else:
            query = models.ComicBook.objects.all()

        query = query.annotate(
            total_pages=Count('comicpage'),
            unread=Case(When(comicstatus__user=user, then='comicstatus__unread')),
            finished=Case(When(comicstatus__user=user, then='comicstatus__finished')),
            last_read_page=Case(When(comicstatus__user=user, then='comicstatus__last_read_page')),
            classification=Case(
                When(directory__isnull=True, then=models.Directory.Classification.C_18),
                default=F('directory__classification'),
                output_field=PositiveSmallIntegerField(choices=models.Directory.Classification.choices)
            )
        )

        query = query.order_by('-date_added')
        return query


class ActionSerializer(serializers.Serializer):
    selectors = serializers.ListSerializer(child=serializers.UUIDField())


class ActionViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'action'
    serializer_class = ActionSerializer

    @action(detail=False, methods=['PUT'])
    def mark_read(self, request):
        serializer = ActionSerializer(data=request.data)
        if serializer.is_valid():
            comics = self.get_comics(serializer.data['selectors'])
            comic_status = models.ComicStatus.objects.filter(comic__selector__in=comics, user=request.user)
            comic_status = comic_status.annotate(total_pages=Count('comic__comicpage'))
            status_to_update = []
            for c_status in comic_status:
                c_status.last_read_page = c_status.total_pages
                c_status.unread = False
                c_status.finished = True
                status_to_update.append(c_status)
                comics.remove(str(c_status.comic_id))
            for new_status in comics:
                comic = models.ComicBook.objects.annotate(
                    total_pages=Count('comicpage')).get(selector=new_status)
                obj, _ = models.ComicStatus.objects.get_or_create(comic=comic, user=request.user)
                obj.unread = False
                obj.finished = True
                obj.last_read_page = comic.total_pages
                status_to_update.append(obj)
            models.ComicStatus.objects.bulk_update(status_to_update, ['unread', 'finished', 'last_read_page'])
            return Response({'status': 'marked_read'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['PUT'])
    def mark_unread(self, request):
        serializer = ActionSerializer(data=request.data)
        if serializer.is_valid():
            serializer = ActionSerializer(data=request.data)
            if serializer.is_valid():
                comics = self.get_comics(serializer.data['selectors'])
                comic_status = models.ComicStatus.objects.filter(comic__selector__in=comics, user=request.user)
                status_to_update = []
                for c_status in comic_status:
                    c_status.last_read_page = 0
                    c_status.unread = True
                    c_status.finished = False
                    status_to_update.append(c_status)
                    comics.remove(str(c_status.comic_id))
                for new_status in comics:
                    comic = models.ComicBook.objects.get(selector=new_status)
                    obj, _ = models.ComicStatus.objects.get_or_create(comic=comic, user=request.user)
                    obj.unread = True
                    obj.finished = False
                    obj.last_read_page = 0
                    status_to_update.append(obj)
                models.ComicStatus.objects.bulk_update(status_to_update, ['unread', 'finished', 'last_read_page'])
                return Response({'status': 'marked_unread'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def get_comics(self, selectors):
        data = set()
        data = data.union(
            set(models.ComicBook.objects.filter(selector__in=selectors).values_list('selector', flat=True)))
        directories = models.Directory.objects.filter(selector__in=selectors)
        if directories:
            for directory in directories:
                data = data.union(
                    set(models.ComicBook.objects.filter(directory=directory).values_list('selector', flat=True)))
            data = data.union(self.get_comics(models.Directory.objects.filter(
                parent__in=directories).values_list('selector', flat=True)))
        return [str(x) for x in data]


class RSSSerializer(serializers.Serializer):
    feed_id = serializers.UUIDField()


class RSSViewSet(viewsets.ViewSet):
    serializer_class = RSSSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user_misc = models.UserMisc.objects.get(user=request.user)
        queryset = {
            "feed_id": user_misc.feed_id
        }
        serializer = self.serializer_class(queryset)
        return Response(serializer.data)
