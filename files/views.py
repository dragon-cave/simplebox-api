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
    GenericFileSerializer,
    ImageFileSerializer,
    VideoFileSerializer,
    AudioFileSerializer
)
from .permissions import IsPrivateSubnet
from aws.s3_objects import upload_file, delete_file

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

        queryset = GenericFile.objects.all()

        if 'image' in types:
            queryset |= ImageFile.objects.all()
        if 'video' in types:
            queryset |= VideoFile.objects.all()
        if 'audio' in types:
            queryset |= AudioFile.objects.all()
        
        if not types:
            queryset = GenericFile.objects.all() | ImageFile.objects.all() | VideoFile.objects.all() | AudioFile.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__name__icontains=search)
            ).distinct()

        return queryset

    def get_serializer_class(self):
        types = self.request.query_params.get('type', '').split(',')
        if 'image' in types:
            return ImageFileSerializer
        elif 'video' in types:
            return VideoFileSerializer
        elif 'audio' in types:
            return AudioFileSerializer
        return GenericFileSerializer

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            return Response({"error": "Nenhum arquivo enviado."}, status=status.HTTP_400_BAD_REQUEST)
        
        if '/' in uploaded_file.name:
            return Response({"error": "O nome do arquivo não pode conter barras."}, status=status.HTTP_400_BAD_REQUEST)

        file_name = uploaded_file.name
        file_size = uploaded_file.size
        
        file_url = upload_file(uploaded_file, f'users/{request.user.user_id}/files/{file_name}')

        file_instance = GenericFile.objects.create(
            name=file_name,
            size=file_size,
            owner=request.user,
            processed=False
        )

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
    permission_classes = [IsPrivateSubnet]
    
    def post(self, request, *args, **kwargs):
        # Process the webhook data here
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
