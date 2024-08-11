from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticated
from .models import GenericFile, ImageFile, VideoFile, AudioFile, Tag, BaseMediaFile
from .serializers import (
    MixedFileSerializer,
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
    permission_classes = [IsAuthenticated]
    filter_backends = (DjangoFilterBackend,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        types = self.request.query_params.get('type', '').split(',')
        
        # Filter files by ownership
        queryset = Q(owner=user)
        
        # Filter by types
        if 'image' in types:
            queryset |= Q(id__in=ImageFile.objects.filter(owner=user).values_list('id', flat=True))
        if 'video' in types:
            queryset |= Q(id__in=VideoFile.objects.filter(owner=user).values_list('id', flat=True))
        if 'audio' in types:
            queryset |= Q(id__in=AudioFile.objects.filter(owner=user).values_list('id', flat=True))

        if not types or '' in types:
            queryset |= Q(id__in=GenericFile.objects.filter(owner=user).values_list('id', flat=True))
            queryset |= Q(id__in=ImageFile.objects.filter(owner=user).values_list('id', flat=True))
            queryset |= Q(id__in=VideoFile.objects.filter(owner=user).values_list('id', flat=True))
            queryset |= Q(id__in=AudioFile.objects.filter(owner=user).values_list('id', flat=True))
        
        return GenericFile.objects.filter(queryset)

    def list(self, request, *args, **kwargs):
        types = self.request.query_params.get('type', '').split(',')
        search = self.request.query_params.get('search', None)
        user = self.request.user

        queryset = []

        # Filter by types
        if 'image' in types:
            queryset.extend(list(ImageFile.objects.filter(owner=user)))
        if 'video' in types:
            queryset.extend(list(VideoFile.objects.filter(owner=user)))
        if 'audio' in types:
            queryset.extend(list(AudioFile.objects.filter(owner=user)))
        
        # If no specific type is requested, include all
        if not types or '' in types:
            queryset.extend(list(GenericFile.objects.filter(owner=user)))
            queryset.extend(list(ImageFile.objects.filter(owner=user)))
            queryset.extend(list(VideoFile.objects.filter(owner=user)))
            queryset.extend(list(AudioFile.objects.filter(owner=user)))

        # Apply search filter
        if search:
            queryset = [
                obj for obj in queryset
                if search.lower() in obj.name.lower() or
                   search.lower() in (obj.description or '').lower() or
                   any(search.lower() in tag.name.lower() for tag in obj.tags.all())
            ]
            
        queryset.sort(key=lambda x: x.id)

        # Paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MixedFileSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MixedFileSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        file_id = kwargs.get('pk')
        file_instance = None

        for model in [GenericFile, ImageFile, VideoFile, AudioFile]:
            try:
                file_instance = model.objects.get(id=file_id)
                break
            except model.DoesNotExist:
                continue

        if file_instance is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if file_instance.owner.user_id != request.user.user_id:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = MixedFileSerializer(file_instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            return Response({"error": "Nenhum arquivo enviado."}, status=status.HTTP_400_BAD_REQUEST)
        
        if '/' in uploaded_file.name:
            return Response({"error": "O nome do arquivo não pode conter barras."}, status=status.HTTP_400_BAD_REQUEST)

        if BaseMediaFile.objects.filter(
            Q(name=uploaded_file.name) & Q(owner=request.user)
        ).exists():
            return Response({"error": "Um arquivo com o mesmo nome já existe."}, status=status.HTTP_409_CONFLICT)

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

        serializer = MixedFileSerializer(file_instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT method is not allowed.")

    def partial_update(self, request, *args, **kwargs):
        file_id = kwargs.get('pk')
        file_instance = None

        # Try to find the file instance in any of the models
        for model in [GenericFile, ImageFile, VideoFile, AudioFile]:
            try:
                file_instance = model.objects.get(id=file_id)
                break
            except model.DoesNotExist:
                continue

        if file_instance is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if file_instance.owner.user_id != request.user.user_id:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the file is processed
        if not file_instance.processed:
            return Response({"error": "Cannot update. The file is not yet processed."}, status=status.HTTP_400_BAD_REQUEST)

        # Update fields based on the type of file
        data = request.data
        valid_fields = ['tags', 'description', 'genre']

        # Check if any valid fields are present in the request data
        if not any(field in data for field in valid_fields):
            return Response({"error": "Invalid update fields."}, status=status.HTTP_400_BAD_REQUEST)

        # Allow only specific fields to be updated
        if 'description' in data:
            file_instance.description = data['description']
        
        if 'tags' in data:
            tags = data['tags']
            # Process tags and create them if they do not exist
            tag_objects = []
            for tag_name in tags:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                tag_objects.append(tag)
            file_instance.tags.set(tag_objects)
        
        if isinstance(file_instance, (VideoFile, AudioFile)) and 'genre' in data:
            file_instance.genre = data['genre']
        
        file_instance.save()

        serializer = MixedFileSerializer(file_instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        file_id = kwargs.get('pk')
        user = self.request.user
        file_instance = None

        # Try to find the file instance in each model
        for model in [GenericFile, ImageFile, VideoFile, AudioFile]:
            try:
                file_instance = model.objects.get(id=file_id, owner=user)
                break
            except model.DoesNotExist:
                continue

        if file_instance is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if file_instance.owner.user_id != request.user.user_id:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the file is processed
        if not file_instance.processed:
            return Response({"error": "O arquivo ainda está sendo processado."}, status=status.HTTP_400_BAD_REQUEST)

        # Construct the base file path
        base_file_path = f'users/{request.user.user_id}/files/{file_instance.name}'

        # Delete the base file
        delete_file(base_file_path)

        # Delete additional files based on file type
        if isinstance(file_instance, ImageFile) or isinstance(file_instance, VideoFile):
            # Delete the thumbnail
            thumbnail_path = f'{base_file_path}/thumbnail.png'
            delete_file(thumbnail_path)

        if isinstance(file_instance, VideoFile):
            # Delete processed video files
            extension = file_instance.name.split('.')[-1]
            for resolution in ['480p', '720p', '1080p']:
                processed_path = f'{base_file_path}/processed/{resolution}.{extension}'
                delete_file(processed_path)

        # Delete the file instance from the database
        file_instance.delete()

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
            generic_file = GenericFile(
                id=file_id,  # Retain the original ID
                name=file_name,
                size=file_size,
                mime_type=mime_type,
                owner=file_owner,
                processed=True
            )
            generic_file.save()
            serializer = MixedFileSerializer(generic_file)
        
        return Response(serializer.data, status=status.HTTP_200_OK)