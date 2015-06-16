from django.db import models

# Create your models here.

class Setting(models.Model):
    name = models.CharField(max_length=50, unique=True)
    value = models.TextField()

    def __str__(self):

        return '"%s":"%s"' % (self.name, self.value)
