from uuid import UUID

from django.contrib.auth.models import User, Group
from django.db.models import Count, Case, When, F, PositiveSmallIntegerField
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, serializers, mixins, permissions, status, renderers
from rest_framework.decorators import api_view, action
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from comic import models
from comic.util import generate_directory, generate_breadcrumbs_from_path


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


class DirectoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
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


class BrowseViewSet(viewsets.ViewSet):
    serializer_class = BrowseSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'selector'

    def list(self, request):
        queryset = []
        for item in generate_directory(request.user):
            queryset.append({
                "selector": item.obj.selector,
                "title": item.name,
                "progress": item.total_read,
                "total": item.total,
                "type": item.item_type,
                "thumbnail": item.obj.thumbnail
            })
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, selector: UUID):
        queryset = []
        directory = models.Directory.objects.get(selector=selector)
        for item in generate_directory(request.user, directory):
            queryset.append({
                "selector": item.obj.selector,
                "title": item.name,
                "progress": item.total_read,
                "total": item.total,
                "type": item.item_type,
                "thumbnail": item.obj.thumbnail
            })
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


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


class PageSerializer(serializers.Serializer):
    page = serializers.IntegerField()


class SetReadViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PageSerializer
    lookup_field = 'selector'

    @swagger_auto_schema(operation_description="PUT /set_read/{selector}/", request_body=PageSerializer)
    def update(self, request, selector):
        serializer = PageSerializer(data=request.data)

        if serializer.is_valid():
            comic_status, _ = models.ComicStatus.objects.get_or_create(comic__selector=selector, user=request.user)
            comic_status.last_read_page = serializer.data['page']
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
    queryset = models.ComicBook.objects.all().order_by('-date_added')
    serializer_class = RecentComicsSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        query = models.ComicBook.objects.annotate(
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
        return query