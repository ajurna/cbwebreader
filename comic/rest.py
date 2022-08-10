from itertools import chain
from pathlib import Path
from typing import Union
from uuid import UUID

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Count, Case, When, F, PositiveSmallIntegerField, Max, Q

from django.http import FileResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, serializers, mixins, permissions, status, renderers
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.request import Request

from comic import models
from comic.util import generate_breadcrumbs_from_path


class UserSerializer(serializers.ModelSerializer):
    classification = serializers.SlugRelatedField(many=False, read_only=True, slug_field='allowed_to_read', source='usermisc')
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_superuser', 'classification']


class AdminPasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(required=False)


class ClassificationSerializer(serializers.Serializer):
    classification = serializers.IntegerField()

    def validate_classification(self, data):
        if data in models.Directory.Classification:
            return data
        raise serializers.ValidationError('Invalid Classification sent.')



class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(methods=['patch'], detail=True, serializer_class=AdminPasswordResetSerializer)
    def reset_password(self, request: Request, pk: int) -> Response:
        """
        This will return a new password set on the user.
        """
        target_user = get_object_or_404(User, id=pk)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if target_user.username == serializer.data['username']:
                password = User.objects.make_random_password()
                target_user.set_password(password)
                resp_serializer = self.get_serializer({
                    'username': target_user.username,
                    'password': password
                })
                return Response(resp_serializer.data)

        return Response({'errors': ['Invalid request']}, status.HTTP_400_BAD_REQUEST)

    @action(methods=['patch'], detail=True, serializer_class=ClassificationSerializer)
    def set_classification(self, request: Request, pk: int) -> Response:
        """
        API Endpoint that will set the classification on the specified user.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            misc, _ = models.UserMisc.objects.get_or_create(user_id=pk)
            misc.allowed_to_read = serializer.data['classification']
            misc.save()
            return Response(data={'classification': misc.allowed_to_read})
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class UserMiscSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserMisc
        fields = ['user', 'feed_id', 'allowed_to_read']


class UserMiscViewSet(viewsets.ModelViewSet):
    queryset = models.UserMisc.objects.all()
    serializer_class = UserMiscSerializer
    permission_classes = [permissions.IsAdminUser]


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


class BrowseSerializer(serializers.Serializer):
    selector = serializers.UUIDField()
    title = serializers.CharField()
    progress = serializers.IntegerField()
    total = serializers.IntegerField()
    type = serializers.CharField()
    thumbnail = serializers.FileField()
    classification = serializers.IntegerField()
    finished = serializers.BooleanField()
    unread = serializers.BooleanField()


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
                                                       comicbook__comicstatus__user=user), distinct=True),
            finished=Q(total=F('progress')),
            unread=Q(total__gt=F('progress'))
        )
        files.extend(dir_db_query)

        # Create Missing Status
        new_status = [models.ComicStatus(comic=file, user=user) for file in
                      file_db_query.exclude(comicstatus__in=models.ComicStatus.objects.filter(
                          comic__in=file_db_query, user=user))]
        models.ComicStatus.objects.bulk_create(new_status)

        file_db_query = file_db_query.annotate(
            total=Count('comicpage', distinct=True),
            progress=F('comicstatus__last_read_page') + 1,
            finished=F('comicstatus__finished'),
            unread=F('comicstatus__unread'),
            user=F('comicstatus__user'),
            classification=Case(
                When(directory__isnull=True, then=models.Directory.Classification.C_G),
                default=F('directory__classification'),
                output_field=PositiveSmallIntegerField(choices=models.Directory.Classification.choices)
            )
        ).filter(Q(user__isnull=True) | Q(user=user.id))

        files.extend(file_db_query)

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

class DirectionSerializer(serializers.Serializer):
    route = serializers.ChoiceField(choices=['read', 'browse'])
    selector = serializers.UUIDField(required=False)

class ReadSerializer(serializers.Serializer):
    selector = serializers.UUIDField()
    title = serializers.CharField()
    last_read_page = serializers.IntegerField()
    prev_comic = DirectionSerializer()
    next_comic = DirectionSerializer()
    pages = PageSerializer(many=True)


class TypeSerializer(serializers.Serializer):
    type = serializers.CharField()


class ReadViewSet(viewsets.ViewSet):
    serializer_class = ReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'selector'

    @swagger_auto_schema(responses={status.HTTP_200_OK: ReadSerializer})
    def retrieve(self, request: Request, selector: UUID) -> Response:
        comic = get_object_or_404(models.ComicBook, selector=selector)
        misc, _ = models.UserMisc.objects.get_or_create(user=request.user)
        pages = models.ComicPage.objects.filter(Comic=comic)
        comic_status, _ = models.ComicStatus.objects.get_or_create(comic=comic, user=request.user)
        comic_list = list(models.ComicBook.objects.filter(directory=comic.directory).order_by('file_name'))
        comic_index = comic_list.index(comic)
        try:
            prev_comic = {'route': 'browse', 'selector': comic.directory.selector} if comic_index == 0 else \
                {'route': 'read', 'selector': comic_list[comic_index-1].selector}
        except AttributeError:
            prev_comic = {'route': 'browse'}
        try:
            next_comic = {'route': 'browse', 'selector': comic.directory.selector} if comic_index+1 == len(comic_list) \
                else {'route': 'read', 'selector': comic_list[comic_index+1].selector}
        except AttributeError:
            next_comic = {'route': 'browse'}
        data = {
            "selector": comic.selector,
            "title": comic.file_name,
            "last_read_page": comic_status.last_read_page,
            "prev_comic": prev_comic,
            "next_comic": next_comic,
            "pages": pages,
        }
        serializer = self.serializer_class(data)
        return Response(serializer.data)

    @swagger_auto_schema(responses={status.HTTP_200_OK: 'PDF Binary Data',
                                    status.HTTP_400_BAD_REQUEST: 'User below classification allowed'})
    @action(methods=['get'], detail=True)
    def pdf(self, request: Request, selector: UUID) -> Union[FileResponse, Response]:
        book = models.ComicBook.objects.get(selector=selector)
        misc, _ = models.UserMisc.objects.get_or_create(user=request.user)
        try:
            if book.directory.classification > misc.allowed_to_read:
                return Response(status=400, data={'errors': 'Not allowed to read.'})
        except AttributeError:
            pass
        return FileResponse(open(book.get_pdf(), 'rb'), content_type='application/pdf')

    @swagger_auto_schema(responses={status.HTTP_200_OK: TypeSerializer})
    @action(methods=['get'], detail=True)
    def type(self, request: Request, selector: UUID) -> Response:
        book = models.ComicBook.objects.get(selector=selector)
        return Response({'type': book.file_name.split('.')[-1].lower()})


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
            last_read_page=Case(When(comicstatus__user=user, then='comicstatus__last_read_page')) + 1,
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
                c_status.last_read_page = c_status.total_pages-1
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


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_superuser']


class UpdateEmailSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()


class PasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField()
    old_password = serializers.CharField()
    new_password = serializers.CharField(required=False)
    new_password_confirm = serializers.CharField(required=False)

    def validate_new_password(self, data):
        if data == '':
            return data
        try:
            validate_password(data)
        except ValidationError as e:
            raise serializers.ValidationError(e)
        return data

    def validate(self, attrs):
        super().validate(attrs)
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError('New passwords do not match')
        return attrs


class AccountViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'username'
    serializer_class = AccountSerializer

    @swagger_auto_schema(method='patch', responses={200: AccountSerializer})
    @action(detail=False, methods=['PATCH'], serializer_class=PasswordResetSerializer)
    def reset_password(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if request.user.username != serializer.data['username']:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'errors': 'Username does not match account'})
            if not request.user.check_password(serializer.data['old_password']):
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'errors': 'Password Incorrect'})
            request.user.set_password(serializer.data['new_password'])
            request.user.save()
            return Response(AccountSerializer(request.user).data)
        else:
            return Response({"errors": serializer.errors}, status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(method='patch', responses={200: AccountSerializer})
    @action(detail=False, methods=['PATCH'], serializer_class=UpdateEmailSerializer)
    def update_email(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if request.user.username != serializer.data['username']:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'errors': 'Username does not match account'})
            if not request.user.check_password(serializer.data['password']):
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'errors': 'Password Incorrect'})
            request.user.email = serializer.data['email']
            request.user.save()
            account = AccountSerializer(request.user)
            return Response(account.data)
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class DirectorySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Directory
        fields = ['selector', 'classification']


class DirectoryViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = DirectorySerializer
    queryset = models.Directory.objects.all()
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'selector'