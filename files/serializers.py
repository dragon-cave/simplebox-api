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
        fields = BaseMediaFileSerializer.Meta.fields + ['width', 'height', 'color_depth', 'resolution', 'exif_data', 'thumbnail_url']

class VideoFileSerializer(BaseMediaFileSerializer):
    duration = serializers.IntegerField()
    resolution = serializers.CharField(max_length=50)
    frame_rate = serializers.FloatField()
    video_codec = serializers.CharField(max_length=50)
    audio_codec = serializers.CharField(max_length=50)
    bit_rate = serializers.IntegerField()
    thumbnail_url = serializers.URLField()
    quality_versions = serializers.JSONField()
    genre = serializers.CharField(max_length=50, required=False)

    class Meta(BaseMediaFileSerializer.Meta):
        model = VideoFile
        fields = BaseMediaFileSerializer.Meta.fields + ['duration', 'resolution', 'frame_rate', 'video_codec', 'audio_codec', 'bit_rate', 'thumbnail_url', 'quality_versions', 'genre']

class AudioFileSerializer(BaseMediaFileSerializer):
    duration = serializers.IntegerField()
    bit_rate = serializers.IntegerField()
    sample_rate = serializers.IntegerField()
    channels = serializers.IntegerField()
    genre = serializers.CharField(max_length=50, required=False)

    class Meta(BaseMediaFileSerializer.Meta):
        model = AudioFile
        fields = BaseMediaFileSerializer.Meta.fields + ['duration', 'bit_rate', 'sample_rate', 'channels', 'genre']
