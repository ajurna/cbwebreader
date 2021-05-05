import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils.http import urlsafe_base64_encode

from comic.models import ComicBook, ComicPage, ComicStatus, Directory
from comic.util import generate_directory


# from os import path


class ComicBookTests(TestCase):
    def setUp(self):
        settings.COMIC_BOOK_VOLUME = Path(Path.cwd(), 'test_comics')
        User.objects.create_user("test", "test@test.com", "test")
        user = User.objects.first()
        ComicBook.process_comic_book(Path("test1.rar"))
        book = ComicBook.process_comic_book(Path("test2.rar"))
        status = ComicStatus(user=user, comic=book, last_read_page=2, unread=False)
        status.save()
        ComicBook.process_comic_book(Path("test4.rar"))

    def test_comic_processing(self):
        book = ComicBook.objects.get(file_name="test1.rar")
        self.assertEqual(book.file_name, "test1.rar")
        page0 = ComicPage.objects.get(Comic=book, index=0)
        self.assertEqual(page0.page_file_name, "img1.jpg")
        self.assertEqual(page0.content_type, "image/jpeg")
        page1 = ComicPage.objects.get(Comic=book, index=1)
        self.assertEqual(page1.page_file_name, "img2.png")
        self.assertEqual(page1.content_type, "image/png")
        page2 = ComicPage.objects.get(Comic=book, index=2)
        self.assertEqual(page2.page_file_name, "img3.gif")
        self.assertEqual(page2.content_type, "image/gif")
        page3 = ComicPage.objects.get(Comic=book, index=3)
        self.assertEqual(page3.page_file_name, "img4.bmp")
        self.assertEqual(page3.content_type, "image/bmp")
        self.assertEqual(ComicPage.objects.filter(Comic=book).count(), 4)

    def test_page_count(self):
        book = ComicBook.objects.get(file_name="test1.rar")
        self.assertEqual(book.page_count, 4)

    def test_is_last_page(self):
        book = ComicBook.objects.get(file_name="test1.rar")
        self.assertEqual(book.is_last_page(3), True)
        self.assertEqual(book.is_last_page(2), False)

    def test_get_image(self):
        book = ComicBook.objects.get(file_name="test1.rar")
        img, content_type = book.get_image(0)
        self.assertEqual(content_type, "image/jpeg")
        self.assertEqual(img.read(), b"img1.jpg")

    def test_nav_with_folder_above(self):
        user = User.objects.get(username="test")
        generate_directory(user)
        book = ComicBook.objects.get(file_name="test1.rar")

        nav = book.nav(user)

        self.assertEqual(nav['prev_path'], "")
        self.assertEqual(nav['cur_path'], urlsafe_base64_encode(book.selector.bytes))

    def test_nav_with_comic_above(self):
        user = User.objects.get(username="test")
        generate_directory(user)
        prev_book = ComicBook.objects.get(file_name="test1.rar", directory__isnull=True)
        book = ComicBook.objects.get(file_name="test2.rar", directory__isnull=True)
        next_book = ComicBook.objects.get(file_name="test3.rar", directory__isnull=True)

        nav = book.nav(user)

        self.assertEqual(nav['prev_path'], urlsafe_base64_encode(prev_book.selector.bytes))
        self.assertEqual(nav['cur_path'], urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav['next_path'], urlsafe_base64_encode(next_book.selector.bytes))

    def test_nav_with_comic_below(self):
        user = User.objects.get(username="test")
        generate_directory(user)
        book = ComicBook.objects.get(file_name="test1.rar", directory__isnull=True)
        next_book = ComicBook.objects.get(file_name="test2.rar", directory__isnull=True)
        nav = book.nav(user)

        self.assertEqual(nav['cur_path'], urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav['next_path'], urlsafe_base64_encode(next_book.selector.bytes))

    def test_nav_with_nothing_below(self):
        user = User.objects.get(username="test")
        generate_directory(user)
        book = ComicBook.objects.get(file_name="test4.rar")
        nav = book.nav(user)

        self.assertEqual(nav['cur_path'], urlsafe_base64_encode(book.selector.bytes))
        self.assertEqual(nav['next_path'], "")

    def test_generate_directory(self):
        user = User.objects.get(username="test")
        folders = generate_directory(user)
        dir1 = folders[0]
        self.assertEqual(dir1.name, "test_folder")
        self.assertEqual(dir1.item_type, "Directory")

        dir2 = folders[1]
        self.assertEqual(dir2.name, "test1.rar")
        self.assertEqual(dir2.item_type, "ComicBook")

        dir3 = folders[2]
        self.assertEqual(dir3.name, "test2.rar")
        self.assertEqual(dir2.item_type, "ComicBook")

        dir4 = folders[3]
        self.assertEqual(dir4.name, "test3.rar")
        self.assertEqual(dir4.item_type, "ComicBook")

    def test_pages(self):
        book = ComicBook.objects.get(file_name="test1.rar")
        pages = [cp for cp in ComicPage.objects.filter(Comic=book).order_by("index")]
        self.assertEqual(pages[0].page_file_name, "img1.jpg")
        self.assertEqual(pages[0].index, 0)
        self.assertEqual(pages[1].page_file_name, "img2.png")
        self.assertEqual(pages[1].index, 1)
        self.assertEqual(pages[2].page_file_name, "img3.gif")
        self.assertEqual(pages[2].index, 2)
        self.assertEqual(pages[3].page_file_name, "img4.bmp")
        self.assertEqual(pages[3].index, 3)


    def test_comic_list(self):
        c = Client()
        response = c.get("/comic/")
        self.assertEqual(response.status_code, 302)
        c.login(username="test", password="test")
        response = c.get("/comic/")
        self.assertEqual(response.status_code, 200)
        user = User.objects.first()
        generate_directory(user)
        directory = Directory.objects.first()
        response = c.get(f"/comic/{urlsafe_base64_encode(directory.selector.bytes)}/")
        self.assertEqual(response.status_code, 200)

    def test_recent_comics(self):
        c = Client()
        response = c.get("/comic/recent/")
        self.assertEqual(response.status_code, 302)

        c.login(username="test", password="test")

        response = c.get("/comic/recent/")
        self.assertEqual(response.status_code, 200)

    def test_recent_comics_json(self):
        c = Client()
        response = c.post("/comic/recent/json/")
        self.assertEqual(response.status_code, 302)

        c.login(username="test", password="test")
        user = User.objects.get(username="test")
        folders = generate_directory(user)

        req_data = {"start": "0", "length": "10", "search[value]": "", "order[0][dir]": "desc"}
        response = c.post("/comic/recent/json/", req_data)
        self.assertEqual(response.status_code, 200)
        req_data["search[value]"] = "test1.rar"
        response = c.post("/comic/recent/json/", req_data)
        self.assertEqual(response.status_code, 200)
        self.maxDiff = None
        book = ComicBook.objects.get(file_name="test1.rar")
        self.assertDictEqual(
            json.loads(response.content),
            {
                "data": [
                    {
                        "date": book.date_added.strftime("%d/%m/%y-%H:%M"),
                        "icon": '<span class="fa fa-book"></span>',
                        "label": '<center><span class="label ' 'label-default">Unread</span></center>',
                        "name": "test1.rar",
                        "selector": urlsafe_base64_encode(book.selector.bytes),
                        "type": "book",
                        "url": f"/comic/read/" f"{urlsafe_base64_encode(book.selector.bytes)}/",
                    }
                ],
                "recordsFiltered": 1,
                "recordsTotal": 4,
            },
        )
        req_data["search[value]"] = ""
        req_data["order[0][dir]"] = 3
        response = c.post("/comic/recent/json/", req_data)
        self.assertEqual(response.status_code, 200)

    def test_comic_edit(self):
        c = Client()
        book: ComicBook = ComicBook.objects.first()
        user = User.objects.get(username="test")

        response = c.get("/comic/edit/")
        self.assertEqual(response.status_code, 302)
        c.login(username="test", password="test")

        response = c.get("/comic/edit/")
        self.assertEqual(response.status_code, 405)

        req_data = {"comic_list_length": 10, "func": "unread", "selected": book.url_safe_selector}
        response = c.post("/comic/edit/", req_data)
        self.assertEqual(response.status_code, 200)

        status = ComicStatus.objects.get(comic=book, user=user)
        self.assertEqual(status.last_read_page, 0)
        self.assertTrue(status.unread)
        self.assertFalse(status.finished)

        req_data["func"] = "read"
        response = c.post("/comic/edit/", req_data)
        self.assertEqual(response.status_code, 200)
        status.refresh_from_db()
        self.assertEqual(status.last_read_page, 3)
        self.assertFalse(status.unread)
        self.assertTrue(status.finished)

        req_data["func"] = "choose"
        response = c.post("/comic/edit/", req_data)
        self.assertEqual(response.status_code, 200)
        status.refresh_from_db()
        self.assertEqual(status.last_read_page, 3)
        self.assertFalse(status.unread)
        self.assertTrue(status.finished)

        del req_data["selected"]
        response = c.post("/comic/edit/", req_data)
        self.assertEqual(response.status_code, 200)

    def test_account_page(self):
        c = Client()
        user = User.objects.get(username="test")
        self.assertEqual(user.username, "test")
        response = c.get("/comic/account/")
        self.assertEqual(response.status_code, 302)

        c.login(username="test", password="test")

        response = c.get("/comic/account/")
        self.assertEqual(response.status_code, 200)

    def test_file_not_in_archive(self):
        c = Client()
        user = User.objects.get(username="test")
        book = ComicBook.objects.get(file_name='test1.rar')
        page = ComicPage.objects.get(Comic=book, index=0)
        page.page_file_name = 'doesnt_exist'
        page.save()
        generate_directory(user)
        c.login(username="test", password="test")
        book.verify_pages()
        response = c.get(f"/comic/read/{urlsafe_base64_encode(book.selector.bytes)}/0/img")
        self.assertEqual(response.status_code, 200)

    def test_duplicate_pages(self):
        c = Client()
        user = User.objects.get(username="test")
        generate_directory(user)
        book = ComicBook.objects.get(file_name='test1.rar')
        page = ComicPage.objects.get(Comic=book, index=0)
        dup_page = ComicPage(Comic=book, index=0, page_file_name=page.page_file_name, content_type=page.content_type)
        dup_page.save()
        c.login(username="test", password="test")
        book.verify_pages()
        response = c.get(f"/comic/read/{urlsafe_base64_encode(book.selector.bytes)}/0/img")
        self.assertEqual(response.status_code, 200)
