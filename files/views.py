from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import BaseMediaFile, ImageFile, VideoFile, AudioFile
from .serializers import (
    BaseMediaFileSerializer,
    ImageFileSerializer,
    VideoFileSerializer,
    AudioFileSerializer
)
from .permissions import IsPrivateSubnet
from aws.s3_objects import upload_file


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class FileViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    pagination_class = StandardResultsSetPagination
    ordering_fields = '__all__'

    def get_queryset(self):
        types = self.request.query_params.get('type', '').split(',')
        search = self.request.query_params.get('search', None)

        queryset = ImageFile.objects.none()

        if 'image' in types:
            queryset |= ImageFile.objects.all()
        if 'video' in types:
            queryset |= VideoFile.objects.all()
        if 'audio' in types:
            queryset |= AudioFile.objects.all()
        
        if not types:
            queryset = ImageFile.objects.all() | VideoFile.objects.all() | AudioFile.objects.all()
        
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
        return ImageFileSerializer

class WebhookView(APIView):
    permission_classes = [IsPrivateSubnet([ '10.0.128.0/20', '10.0.144.0/20' ])]
    
    def post(self, request, *args, **kwargs):
        # Process the webhook data here
        return Response({'status': 'success'}, status=status.HTTP_200_OK)

class FileUploadView(APIView):
    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        file_name = uploaded_file.name
        file_url = upload_file(uploaded_file, file_name)
        
        file_instance = BaseMediaFile.objects.create(
            name=file_name,
            user=request.user,
            processed=False
        )

        serializer = BaseMediaFileSerializer(file_instance)

        return Response({"file_url": file_url, "file": serializer.data}, status=status.HTTP_201_CREATED)