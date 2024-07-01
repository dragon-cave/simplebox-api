from django.db import models

class Image(models.Model):
    title = models.CharField(max_length=100)
    image = models.FileField()
    def __str__(self):
        return self.title
