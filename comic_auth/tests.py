from django.test import TestCase
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from comic.models import ComicBook, ComicPage, Setting
from os import path
import os

# Create your tests here.

class ComicBookTests(TestCase):
    def setUp(self):
        ComicBook.process_comic_book(os.getcwd(), path.join('comic', 'test', 'test1.rar'), 'test1.rar')
        book = ComicBook.process_comic_book(os.getcwd(), path.join('comic', 'test', 'test2.rar'), 'test2.rar')
        book.last_read_page = 2
        book.unread = False
        book.save()
        ComicBook.process_comic_book(os.getcwd(), path.join('comic', 'test', 'test4.rar'), 'test4.rar')
        Setting(name='BASE_DIR', value=os.getcwd()).save()

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
        comic_path = path.join(os.getcwd(), 'comic', 'test', 'test1.rar')
        img, content_type = book.get_image(comic_path, 0)
        self.assertEqual(content_type, 'image/jpeg')
        self.assertEqual(img.read(), 'img1.jpg')

    def test_nav_first_page_with_folder_above(self):
        book = ComicBook.objects.get(file_name='test1.rar')
        comic_path = path.join('comic', 'test', 'test1.rar')
        encoded_path = urlsafe_base64_encode(comic_path)
        prev_path_encoded = urlsafe_base64_encode(path.join('comic','test'))
        nav = book.nav(encoded_path, 0)
        self.assertEqual(nav.next_index, 1)
        self.assertEqual(nav.next_path, encoded_path)
        self.assertEqual(nav.prev_index, -1)
        self.assertEqual(nav.prev_path, prev_path_encoded)
        self.assertEqual(nav.cur_index, 0)
        self.assertEqual(nav.cur_path, encoded_path)
        self.assertEqual(nav.q_prev_to_directory, True)
        self.assertEqual(nav.q_next_to_directory, False)

    def test_nav_first_page_with_comic_above(self):
        book = ComicBook.objects.get(file_name='test2.rar')
        comic_path = path.join('comic', 'test', 'test2.rar')
        encoded_path = urlsafe_base64_encode(comic_path)
        prev_path_encoded = urlsafe_base64_encode(path.join('comic', 'test', 'test1.rar'))
        nav = book.nav(encoded_path, 0)
        self.assertEqual(nav.next_index, 1)
        self.assertEqual(nav.next_path, encoded_path)
        self.assertEqual(nav.prev_index, 3)
        self.assertEqual(nav.prev_path, prev_path_encoded)
        self.assertEqual(nav.cur_index, 0)
        self.assertEqual(nav.cur_path, encoded_path)
        self.assertEqual(nav.q_prev_to_directory, False)
        self.assertEqual(nav.q_next_to_directory, False)

    def test_nav_last_page_with_comic_below(self):
        book = ComicBook.objects.get(file_name='test2.rar')
        comic_path = path.join('comic', 'test', 'test2.rar')
        encoded_path = urlsafe_base64_encode(comic_path)
        next_path_encoded = urlsafe_base64_encode(path.join('comic', 'test', 'test3.rar'))
        nav = book.nav(encoded_path, 3)
        self.assertEqual(nav.next_index, 0)
        self.assertEqual(nav.next_path, next_path_encoded)
        self.assertEqual(nav.prev_index, 2)
        self.assertEqual(nav.prev_path, encoded_path)
        self.assertEqual(nav.cur_index, 3)
        self.assertEqual(nav.cur_path, encoded_path)
        self.assertEqual(nav.q_prev_to_directory, False)
        self.assertEqual(nav.q_next_to_directory, False)

    def test_nav_last_page_with_nothing_below(self):
        book = ComicBook.objects.get(file_name='test4.rar')
        comic_path = path.join('comic', 'test', 'test4.rar')
        encoded_path = urlsafe_base64_encode(comic_path)
        next_path_encoded = urlsafe_base64_encode(path.join('comic', 'test'))
        nav = book.nav(encoded_path, 3)
        self.assertEqual(nav.next_index, -1)
        self.assertEqual(nav.next_path, next_path_encoded)
        self.assertEqual(nav.prev_index, 2)
        self.assertEqual(nav.prev_path, encoded_path)
        self.assertEqual(nav.cur_index, 3)
        self.assertEqual(nav.cur_path, encoded_path)
        self.assertEqual(nav.q_prev_to_directory, False)
        self.assertEqual(nav.q_next_to_directory, True)

    def test_nav_in_comic(self):
        book = ComicBook.objects.get(file_name='test1.rar')
        comic_path = path.join('comic', 'test', 'test1.rar')
        encoded_path = urlsafe_base64_encode(comic_path)
        nav = book.nav(encoded_path, 1)
        self.assertEqual(nav.next_index, 2)
        self.assertEqual(nav.next_path, encoded_path)
        self.assertEqual(nav.prev_index, 0)
        self.assertEqual(nav.prev_path, encoded_path)
        self.assertEqual(nav.cur_index, 1)
        self.assertEqual(nav.cur_path, encoded_path)
        self.assertEqual(nav.q_prev_to_directory, False)
        self.assertEqual(nav.q_next_to_directory, False)

    def test_generate_directory(self):
        #self.name = ''
        #self.isdir = False
        #self.icon = ''
        #self.iscb = False
        #self.location = ''
        #self.label = ''
        #self.cur_page = 0
        base_dir = Setting.objects.get(name='BASE_DIR').value

        folders = ComicBook.generate_directory(base_dir, path.join('comic', 'test'))
        #should be 4 items in list.
        dir1 = folders[0]
        self.assertEqual(dir1.name, 'test_folder')
        self.assertTrue(dir1.isdir)
        self.assertEqual(dir1.icon, 'glyphicon-folder-open')
        self.assertFalse(dir1.iscb)
        location = urlsafe_base64_encode(path.join('comic', 'test', 'test_folder'))
        self.assertEqual(dir1.location, location)
        self.assertEqual(dir1.label, '')
        self.assertEqual(dir1.cur_page, 0)

        dir2 = folders[1]
        self.assertEqual(dir2.name, 'test1.rar')
        self.assertFalse(dir2.isdir)
        self.assertEqual(dir2.icon, 'glyphicon-book')
        self.assertTrue(dir2.iscb)
        location = urlsafe_base64_encode(path.join('comic', 'test', 'test1.rar'))
        self.assertEqual(dir2.location, location)
        self.assertEqual(dir2.label, '<span class="label label-default pull-right">Unread</span>')
        self.assertEqual(dir2.cur_page, 0)

        dir3 = folders[2]
        self.assertEqual(dir3.name, 'test2.rar')
        self.assertFalse(dir3.isdir)
        self.assertEqual(dir3.icon, 'glyphicon-book')
        self.assertTrue(dir3.iscb)
        location = urlsafe_base64_encode(path.join('comic', 'test', 'test2.rar'))
        self.assertEqual(dir3.location, location)
        self.assertEqual(dir3.label, '<span class="label label-primary pull-right">3/4</span>')
        self.assertEqual(dir3.cur_page, 2)

        dir3 = folders[3]
        self.assertEqual(dir3.name, 'test3.rar')
        self.assertFalse(dir3.isdir)
        self.assertEqual(dir3.icon, 'glyphicon-book')
        self.assertTrue(dir3.iscb)
        location = urlsafe_base64_encode(path.join('comic', 'test', 'test3.rar'))
        self.assertEqual(dir3.location, location)
        self.assertEqual(dir3.label, '<span class="label label-danger pull-right">Unprocessed</span>')
        self.assertEqual(dir3.cur_page, 0)

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






































