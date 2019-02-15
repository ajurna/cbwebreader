import json
import os
from os import path

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils.http import urlsafe_base64_encode

from comic.models import ComicBook, ComicPage, Setting, ComicStatus, Directory
from comic.util import generate_directory


# Create your tests here.


class ComicBookTests(TestCase):
    def setUp(self):
        Setting.objects.create(name='BASE_DIR', value=path.join(os.getcwd(), 'comic', 'test'))
        User.objects.create_user('test', 'test@test.com', 'test')
        user = User.objects.first()
        ComicBook.process_comic_book('test1.rar')
        book = ComicBook.process_comic_book('test2.rar')
        status = ComicStatus(user=user,
                             comic=book,
                             last_read_page=2,
                             unread=False)
        status.save()
        ComicBook.process_comic_book('test4.rar')

    def test_comic_processing(self):
        book = ComicBook.objects.get(file_name='test1.rar')
        self.assertEqual(book.file_name, 'test1.rar')
        page0 = ComicPage.objects.get(Comic=book, index=0)
        self.assertEqual(page0.page_file_name, 'img1.jpg')
        self.assertEqual(page0.content_type, 'image/jpeg')
        page1 = ComicPage.objects.get(Comic=book, index=1)
        self.assertEqual(page1.page_file_name, 'img2.png')
        self.assertEqual(page1.content_type, 'image/png')
        page2 = ComicPage.objects.get(Comic=book, index=2)
        self.assertEqual(page2.page_file_name, 'img3.gif')
        self.assertEqual(page2.content_type, 'image/gif')
        page3 = ComicPage.objects.get(Comic=book, index=3)
        self.assertEqual(page3.page_file_name, 'img4.bmp')
        self.assertEqual(page3.content_type, 'image/bmp')
        self.assertEqual(ComicPage.objects.filter(Comic=book).count(), 4)

    def test_page_count(self):
        book = ComicBook.objects.get(file_name='test1.rar')
        self.assertEqual(book.page_count, 4)

    def test_is_last_page(self):
        book = ComicBook.objects.get(file_name='test1.rar')
        self.assertEqual(book.is_last_page(3), True)
        self.assertEqual(book.is_last_page(2), False)

    def test_get_image(self):
        book = ComicBook.objects.get(file_name='test1.rar')
        img, content_type = book.get_image(0)
        self.assertEqual(content_type, 'image/jpeg')
        self.assertEqual(img.read(), b'img1.jpg')

    def test_nav_first_page_with_folder_above(self):
        book = ComicBook.objects.get(file_name='test1.rar')
        user = User.objects.get(username='test')
        nav = book.nav(0, user)
        self.assertEqual(nav.next_index, 1)
        self.assertEqual(nav.next_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.prev_index, -1)
        self.assertEqual(nav.prev_path, '')
        self.assertEqual(nav.cur_index, 0)
        self.assertEqual(nav.cur_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.q_prev_to_directory, True)
        self.assertEqual(nav.q_next_to_directory, False)

    def test_nav_first_page_with_comic_above(self):
        prev_book = ComicBook.objects.get(file_name='test1.rar')
        book = ComicBook.objects.get(file_name='test2.rar',
                                     directory__isnull=True)
        user = User.objects.get(username='test')

        nav = book.nav(0, user)
        self.assertEqual(nav.next_index, 1)
        self.assertEqual(nav.next_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.prev_index, 0)
        self.assertEqual(nav.prev_path.encode(), urlsafe_base64_encode(prev_book.selector.bytes))
        self.assertEqual(nav.cur_index, 0)
        self.assertEqual(nav.cur_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.q_prev_to_directory, False)
        self.assertEqual(nav.q_next_to_directory, False)

    def test_nav_last_page_with_comic_below(self):
        user = User.objects.get(username='test')
        book = ComicBook.objects.get(file_name='test1.rar',
                                     directory__isnull=True)
        next_book = ComicBook.objects.get(file_name='test2.rar',
                                          directory__isnull=True)
        nav = book.nav(3, user)
        self.assertEqual(nav.next_index, 2)
        self.assertEqual(nav.next_path.encode(), urlsafe_base64_encode(next_book.selector.bytes))
        self.assertEqual(nav.prev_index, 2)
        self.assertEqual(nav.prev_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.cur_index, 3)
        self.assertEqual(nav.cur_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.q_prev_to_directory, False)
        self.assertEqual(nav.q_next_to_directory, False)

    def test_nav_last_page_with_nothing_below(self):
        user = User.objects.get(username='test')
        book = ComicBook.objects.get(file_name='test4.rar')
        nav = book.nav(3, user)
        self.assertEqual(nav.next_index, -1)
        self.assertEqual(nav.next_path, '')
        self.assertEqual(nav.prev_index, 2)
        self.assertEqual(nav.prev_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.cur_index, 3)
        self.assertEqual(nav.cur_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.q_prev_to_directory, False)
        self.assertEqual(nav.q_next_to_directory, True)

    def test_nav_in_comic(self):
        user = User.objects.get(username='test')
        book = ComicBook.objects.get(file_name='test1.rar',
                                     directory__isnull=True)
        nav = book.nav(1, user)
        self.assertEqual(nav.next_index, 2)
        self.assertEqual(nav.next_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.prev_index, 0)
        self.assertEqual(nav.prev_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.cur_index, 1)
        self.assertEqual(nav.cur_path.encode(), urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav.q_prev_to_directory, False)
        self.assertEqual(nav.q_next_to_directory, False)

    def test_generate_directory(self):
        user = User.objects.get(username='test')
        folders = generate_directory(user)
        dir1 = folders[0]
        self.assertEqual(dir1.name, 'test_folder')
        self.assertEqual(dir1.type, 'directory')
        self.assertEqual(dir1.icon, 'glyphicon-folder-open')
        d = Directory.objects.get(name='test_folder',
                                  parent__isnull=True)
        location = '/comic/{0}/'.format(urlsafe_base64_encode(d.selector.bytes).decode())
        self.assertEqual(dir1.location, location)
        self.assertEqual(dir1.label, '<center><span class="label label-default">Empty</span></center>')

        dir2 = folders[1]
        self.assertEqual(dir2.name, 'test1.rar')
        self.assertEqual(dir2.type, 'book')
        self.assertEqual(dir2.icon, 'glyphicon-book')
        c = ComicBook.objects.get(file_name='test1.rar',
                                  directory__isnull=True)
        location = '/comic/read/{0}/{1}/'.format(urlsafe_base64_encode(c.selector.bytes).decode(),
                                                 '0')
        self.assertEqual(dir2.location, location)
        self.assertEqual(dir2.label, '<center><span class="label label-default">Unread</span></center>')

        dir3 = folders[2]
        self.assertEqual(dir3.name, 'test2.rar')
        self.assertEqual(dir3.type, 'book')
        self.assertEqual(dir3.icon, 'glyphicon-book')
        c = ComicBook.objects.get(file_name='test2.rar',
                                  directory__isnull=True)
        location = '/comic/read/{0}/{1}/'.format(urlsafe_base64_encode(c.selector.bytes).decode(),
                                                 '2')
        self.assertEqual(dir3.location, location)
        self.assertEqual(dir3.label, '<center><span class="label label-primary">3/4</span></center>')

        dir4 = folders[3]
        self.assertEqual(dir4.name, 'test3.rar')
        self.assertEqual(dir4.type, 'book')
        self.assertEqual(dir3.icon, 'glyphicon-book')
        c = ComicBook.objects.get(file_name='test3.rar',
                                  directory__isnull=True)
        location = '/comic/read/{0}/{1}/'.format(urlsafe_base64_encode(c.selector.bytes).decode(),
                                                 '0')
        self.assertEqual(dir4.location, location)
        self.assertEqual(dir4.label, '<center><span class="label label-default">Unread</span></center>')

    def test_pages(self):
        book = ComicBook.objects.get(file_name='test1.rar')
        pages = book.pages
        self.assertEqual(pages[0].page_file_name, 'img1.jpg')
        self.assertEqual(pages[0].index, 0)
        self.assertEqual(pages[1].page_file_name, 'img2.png')
        self.assertEqual(pages[1].index, 1)
        self.assertEqual(pages[2].page_file_name, 'img3.gif')
        self.assertEqual(pages[2].index, 2)
        self.assertEqual(pages[3].page_file_name, 'img4.bmp')
        self.assertEqual(pages[3].index, 3)

    def test_page_name(self):
        book = ComicBook.objects.get(file_name='test1.rar')
        self.assertEqual(book.page_name(0), 'img1.jpg')

    def test_comic_list(self):
        c = Client()
        response = c.get('/comic/')
        self.assertEqual(response.status_code, 302)
        c.login(username='test', password='test')
        response = c.get('/comic/')
        self.assertEqual(response.status_code, 200)
        user = User.objects.first()
        generate_directory(user)
        directory = Directory.objects.first()
        response = c.get(f'/comic/{urlsafe_base64_encode(directory.selector.bytes).decode()}/')
        self.assertEqual(response.status_code, 200)

    def test_comic_list_json(self):
        c = Client()
        response = c.post('/comic/list_json/')
        self.assertEqual(response.status_code, 302)

        c.login(username='test', password='test')
        response = c.post('/comic/list_json/')
        self.assertEqual(response.status_code, 200)
        directory = Directory.objects.first()
        response = c.post(f'/comic/list_json/{urlsafe_base64_encode(directory.selector.bytes).decode()}/')
        self.assertEqual(response.status_code, 200)

    def test_recent_comics(self):
        c = Client()
        response = c.get('/comic/recent/')
        self.assertEqual(response.status_code, 302)

        c.login(username='test', password='test')

        response = c.get('/comic/recent/')
        self.assertEqual(response.status_code, 200)

    def test_recent_comics_json(self):
        c = Client()
        response = c.post('/comic/recent/json/')
        self.assertEqual(response.status_code, 302)

        c.login(username='test', password='test')
        generate_directory(User.objects.first())
        ComicStatus.objects.all().delete()

        req_data = {
            'start': '0',
            'length': '10',
            'search[value]': '',
            'order[0][dir]': 'desc'
        }
        response = c.post('/comic/recent/json/', req_data)
        self.assertEqual(response.status_code, 200)
        req_data['search[value]'] = 'test1.rar'
        response = c.post('/comic/recent/json/', req_data)
        self.assertEqual(response.status_code, 200)
        self.maxDiff = None
        book = ComicBook.objects.get(file_name='test1.rar')
        self.assertDictEqual(json.loads(response.content),
                             {'data': [{'date': book.date_added.strftime('%d/%m/%y-%H:%M'),
                                        'icon': '<span class="glyphicon glyphicon-book"></span>',
                                        'label': '<center><span class="label '
                                                 'label-default">Unread</span></center>',
                                        'name': 'test1.rar',
                                        'selector': urlsafe_base64_encode(book.selector.bytes).decode(),
                                        'type': 'book',
                                        'url': f'/comic/read/'
                                        f'{urlsafe_base64_encode(book.selector.bytes).decode()}/0/'}],
                              'recordsFiltered': 1,
                              'recordsTotal': 4})
        req_data['search[value]'] = ''
        req_data['order[0][dir]'] = 3
        response = c.post('/comic/recent/json/', req_data)

        self.assertListEqual([x['name'] for x in json.loads(response.content)['data']],
                             ['test1.rar', 'test2.rar', 'test4.rar', 'test3.rar'])

        req_data['order[0][dir]'] = 2
        response = c.post('/comic/recent/json/', req_data)
        self.assertListEqual([x['name'] for x in json.loads(response.content)['data']],
                             ['test1.rar', 'test2.rar', 'test4.rar', 'test3.rar'])

    def test_comic_edit(self):
        c = Client()
        book: ComicBook = ComicBook.objects.first()
        user = User.objects.get(username='test')

        response = c.get('/comic/edit/')
        self.assertEqual(response.status_code, 302)
        c.login(username='test', password='test')

        response = c.get('/comic/edit/')
        self.assertEqual(response.status_code, 405)

        req_data = {"comic_list_length": 10, "func": "unread", "selected": book.selector_string}
        response = c.post('/comic/edit/', req_data)
        self.assertEqual(response.status_code, 200)

        status = ComicStatus.objects.get(comic=book, user=user)
        self.assertEqual(status.last_read_page, 0)
        self.assertTrue(status.unread)
        self.assertFalse(status.finished)

        req_data['func'] = 'read'
        response = c.post('/comic/edit/', req_data)
        self.assertEqual(response.status_code, 200)
        status.refresh_from_db()
        self.assertEqual(status.last_read_page, 3)
        self.assertFalse(status.unread)
        self.assertTrue(status.finished)

        req_data['func'] = 'choose'
        response = c.post('/comic/edit/', req_data)
        self.assertEqual(response.status_code, 200)
        status.refresh_from_db()
        self.assertEqual(status.last_read_page, 3)
        self.assertFalse(status.unread)
        self.assertTrue(status.finished)

        del req_data['selected']
        response = c.post('/comic/edit/', req_data)
        self.assertEqual(response.status_code, 200)

    def test_account_page(self):
        c = Client()
        user = User.objects.get(username='test')

        response = c.get('/comic/account/')
        self.assertEqual(response.status_code, 302)

        c.login(username='test', password='test')

        response = c.get('/comic/account/')
        self.assertEqual(response.status_code, 200)

        response = c.post('/comic/account/')
