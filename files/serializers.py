from rest_framework import serializers
from .models import GenericFile, ImageFile, VideoFile, AudioFile, Tag
from aws.s3_objects import get_presigned_url

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class BaseMediaFileSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        fields = ['id', 'name', 'size', 'upload_date', 'mime_type', 'description', 'tags', 'processed']
        read_only_fields = ['size']

class MixedFileSerializer(serializers.Serializer):
    def to_representation(self, instance):
        file_path = f'users/{instance.owner.id}/files/{instance.name}'

        if isinstance(instance, ImageFile):
            data = ImageFileSerializer(instance).data
            data['thumbnail_url'] = get_presigned_url(f'{file_path}/thumbnail.png')
        elif isinstance(instance, VideoFile):
            data = VideoFileSerializer(instance).data
            data['thumbnail_url'] = get_presigned_url(f'{file_path}/thumbnail.png')
            data['processed_video_urls'] = {
                '480p': get_presigned_url(f'{file_path}/processed/480p.mp4'),
                '720p': get_presigned_url(f'{file_path}/processed/720p.mp4'),
                '1080p': get_presigned_url(f'{file_path}/processed/1080p.mp4'),
            }
        elif isinstance(instance, AudioFile):
            data = AudioFileSerializer(instance).data
        else:
            data = GenericFileSerializer(instance).data
        
        # Format tags as a list of strings
        if 'tags' in data:
            data['tags'] = [tag.name for tag in instance.tags.all()]

        data['url'] = get_presigned_url(file_path)

        return data

class GenericFileSerializer(BaseMediaFileSerializer):
    class Meta(BaseMediaFileSerializer.Meta):
        model = GenericFile
        fields = BaseMediaFileSerializer.Meta.fields

class ImageFileSerializer(BaseMediaFileSerializer):
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    color_depth = serializers.IntegerField()
    resolution = serializers.CharField(max_length=50)
    exif_data = serializers.JSONField()
    class Meta(BaseMediaFileSerializer.Meta):
        model = ImageFile
        fields = BaseMediaFileSerializer.Meta.fields + ['width', 'height', 'color_depth', 'resolution', 'exif_data']

class VideoFileSerializer(BaseMediaFileSerializer):
    duration = serializers.IntegerField()
    resolution = serializers.CharField(max_length=50)
    frame_rate = serializers.FloatField()
    video_codec = serializers.CharField(max_length=50)
    audio_codec = serializers.CharField(max_length=50)
    bit_rate = serializers.IntegerField()
    genre = serializers.CharField(max_length=50, required=False)

    class Meta(BaseMediaFileSerializer.Meta):
        model = VideoFile
        fields = BaseMediaFileSerializer.Meta.fields + ['duration', 'resolution', 'frame_rate', 'video_codec', 'audio_codec', 'bit_rate', 'genre']

class AudioFileSerializer(BaseMediaFileSerializer):
    duration = serializers.IntegerField()
    bit_rate = serializers.IntegerField()
    sample_rate = serializers.IntegerField()
    channels = serializers.IntegerField()
    genre = serializers.CharField(max_length=50, required=False)

    class Meta(BaseMediaFileSerializer.Meta):
        model = AudioFile
        fields = BaseMediaFileSerializer.Meta.fields + ['duration', 'bit_rate', 'sample_rate', 'channels', 'genre']
