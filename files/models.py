from django.db import models

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class BaseMediaFile(models.Model):
    name = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    mime_type = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    tags = models.ManyToManyField('Tag', related_name='%(class)s_media_files')
    owner = models.ForeignKey('user.User', on_delete=models.CASCADE)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class GenericFile(BaseMediaFile):
    def __str__(self):
        return self.name
    
class ImageFile(BaseMediaFile):
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    color_depth = models.PositiveIntegerField()
    resolution = models.CharField(max_length=50)
    exif_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name

class VideoFile(BaseMediaFile):
    duration = models.PositiveIntegerField()
    resolution = models.CharField(max_length=50)
    frame_rate = models.FloatField()
    video_codec = models.CharField(max_length=50)
    audio_codec = models.CharField(max_length=50)
    bit_rate = models.PositiveIntegerField()
    genre = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name

class AudioFile(BaseMediaFile):
    duration = models.PositiveIntegerField()  # duration in seconds
    bit_rate = models.PositiveIntegerField()
    sample_rate = models.PositiveIntegerField()
    channels = models.PositiveIntegerField()
    genre = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name
