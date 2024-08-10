from rest_framework import serializers
from .models import ImageFile, VideoFile, AudioFile, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class BaseMediaFileSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        fields = ['id', 'name', 'file_url', 'size', 'upload_date', 'mime_type', 'description', 'tags']

class ImageFileSerializer(BaseMediaFileSerializer):
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    color_depth = serializers.IntegerField()
    resolution = serializers.CharField(max_length=50)
    exif_data = serializers.JSONField()
    thumbnail_url = serializers.URLField()

    class Meta(BaseMediaFileSerializer.Meta):
        model = ImageFile

class VideoFileSerializer(BaseMediaFileSerializer):
    duration = serializers.IntegerField()
    resolution = serializers.CharField(max_length=50)
    frame_rate = serializers.FloatField()
    video_codec = serializers.CharField(max_length=50)
    audio_codec = serializers.CharField(max_length=50)
    bit_rate = serializers.IntegerField()
    thumbnail_url = serializers.URLField()
    quality_versions = serializers.JSONField()
    genre = serializers.CharField(required=False)

    class Meta(BaseMediaFileSerializer.Meta):
        model = VideoFile

class AudioFileSerializer(BaseMediaFileSerializer):
    duration = serializers.IntegerField()
    bit_rate = serializers.IntegerField()
    sample_rate = serializers.IntegerField()
    channels = serializers.IntegerField()
    genre = serializers.CharField(required=False)

    class Meta(BaseMediaFileSerializer.Meta):
        model = AudioFile