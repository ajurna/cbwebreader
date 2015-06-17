from django.db import models

# Create your models here.

class Setting(models.Model):
    name = models.CharField(max_length=50, unique=True)
    value = models.TextField()

    def __str__(self):

        return '"%s":"%s"' % (self.name, self.value)

class ComicBook(models.Model):
    file_name = models.CharField(max_length=100, unique=True)
    last_read_page = models.IntegerField()

class ComicPage(models.Model):
    Comic = models.ForeignKey(ComicBook)
    index = models.IntegerField()
    page_file_name = models.CharField(max_length=100, unique=False)
    content_type = models.CharField(max_length=30)
