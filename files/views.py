from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import MethodNotAllowed
from .models import GenericFile, ImageFile, VideoFile, AudioFile
from .serializers import (
    BaseMediaFileSerializer,
    GenericFileSerializer,
    ImageFileSerializer,
    VideoFileSerializer,
    AudioFileSerializer
)
from .permissions import IsPrivateSubnet
from aws.s3_objects import upload_file, delete_file
from aws.sqs import enqueue_json_object

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class FileViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    pagination_class = StandardResultsSetPagination
    ordering_fields = '__all__'
    
    def get_queryset(self):
        types = self.request.query_params.get('type', '').split(',')
        search = self.request.query_params.get('search', None)

        queryset = []

        if 'image' in types:
            queryset.extend(ImageFile.objects.all())
        if 'video' in types:
            queryset.extend(VideoFile.objects.all())
        if 'audio' in types:
            queryset.extend(AudioFile.objects.all())
        if 'generic' in types or not types:
            queryset.extend(GenericFile.objects.all())
            queryset.extend(ImageFile.objects.all())
            queryset.extend(VideoFile.objects.all())
            queryset.extend(AudioFile.objects.all())

        if search:
            queryset = [obj for obj in queryset if
                        (search.lower() in obj.name.lower() or
                        search.lower() in (obj.description or '').lower() or
                        any(search.lower() in tag.name.lower() for tag in obj.tags.all()))]

        # Remove duplicates if necessary
        queryset = list({obj.id: obj for obj in queryset}.values())

        return queryset

    def get_serializer_class(self):
        obj = self.get_object()
        if isinstance(obj, ImageFile):
            return ImageFileSerializer
        elif isinstance(obj, VideoFile):
            return VideoFileSerializer
        elif isinstance(obj, AudioFile):
            return AudioFileSerializer
        else:
            return GenericFileSerializer



    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            return Response({"error": "Nenhum arquivo enviado."}, status=status.HTTP_400_BAD_REQUEST)
        
        if '/' in uploaded_file.name:
            return Response({"error": "O nome do arquivo não pode conter barras."}, status=status.HTTP_400_BAD_REQUEST)

        file_name = uploaded_file.name
        file_size = uploaded_file.size
        
        upload_file(uploaded_file, f'users/{request.user.user_id}/files/{file_name}')

        file_instance = GenericFile.objects.create(
            name=file_name,
            size=file_size,
            owner=request.user,
            processed=False
        )

        enqueue_json_object({
            'user_id': request.user.user_id,
            'file_name': file_name,
            'file_id': file_instance.id
        })

        serializer = GenericFileSerializer(file_instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT method is not allowed.")

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PATCH method is not allowed.")

    def destroy(self, request, *args, **kwargs):
        file_id = kwargs.get('pk')
        file_instance = get_object_or_404(GenericFile, id=file_id)

        if not file_instance.processed:
            return Response({"error": "O arquivo ainda está sendo processado."}, status=status.HTTP_400_BAD_REQUEST)

        file_path = f'users/{request.user.user_id}/files/{file_instance.name}'
        file_instance.delete()

        delete_file(file_path)

        return Response(status=status.HTTP_204_NO_CONTENT)

class WebhookView(APIView):
    # permission_classes = [IsPrivateSubnet]
    
    def post(self, request, *args, **kwargs):
        data = request.data
        
        file_id = data.get('file_id')
        mime_type = data.get('mime_type')
        file_data = data.get('data', {})
        
        # Retrieve the GenericFile instance and extract its data
        generic_file_instance = get_object_or_404(GenericFile, id=file_id)
        file_name = generic_file_instance.name
        file_size = generic_file_instance.size
        file_owner = generic_file_instance.owner
        
        # Check if the GenericFile has already been processed
        if generic_file_instance.processed:
            return Response({"error": "File has already been processed."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete the GenericFile instance
        generic_file_instance.delete()
        
        # Create and save media-specific instances
        if mime_type.startswith('image/'):
            # Create and save ImageFile instance
            image_file = ImageFile(
                id=file_id,  # Retain the original ID
                name=file_name,
                size=file_size,
                mime_type=mime_type,
                owner=file_owner,
                width=file_data.get('width'),
                height=file_data.get('height'),
                color_depth=file_data.get('color_depth'),
                resolution=file_data.get('resolution'),
                exif_data=file_data.get('exif_data'),
                processed=True
            )
            image_file.save()
            serializer = ImageFileSerializer(image_file)
        
        elif mime_type.startswith('video/'):
            # Create and save VideoFile instance
            video_file = VideoFile(
                id=file_id,  # Retain the original ID
                name=file_name,
                size=file_size,
                mime_type=mime_type,
                owner=file_owner,
                duration=file_data.get('duration'),
                resolution=file_data.get('resolution'),
                frame_rate=file_data.get('frame_rate'),
                video_codec=file_data.get('video_codec'),
                audio_codec=file_data.get('audio_codec'),
                bit_rate=file_data.get('bit_rate'),
                processed=True
            )
            video_file.save()
            serializer = VideoFileSerializer(video_file)
        
        elif mime_type.startswith('audio/'):
            # Create and save AudioFile instance
            audio_file = AudioFile(
                id=file_id,  # Retain the original ID
                name=file_name,
                size=file_size,
                mime_type=mime_type,
                owner=file_owner,
                duration=file_data.get('duration'),
                bit_rate=file_data.get('bit_rate'),
                sample_rate=file_data.get('sample_rate'),
                channels=file_data.get('channels'),
                processed=True
            )
            audio_file.save()
            serializer = AudioFileSerializer(audio_file)
        
        else:
            return Response({"error": "Unsupported MIME type."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.data, status=status.HTTP_200_OK)