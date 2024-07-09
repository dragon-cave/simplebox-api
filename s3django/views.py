import boto3
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Image
from .serializers import ImageSerializer
import os

class ImageView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        image_serializer = ImageSerializer(data=request.data)
        if image_serializer.is_valid():
            s3_client = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                           aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                                           aws_session_token=os.getenv('AWS_SESSION_TOKEN'))
            file_obj = request.FILES['image']
            s3_client.upload_fileobj(
                file_obj,
                os.getenv('AWS_STORAGE_BUCKET_NAME'),
                file_obj.name,
                # ExtraArgs={'ACL': 'public-read', 'ContentType': file_obj.content_type}
            )
            return Response(image_serializer.data, status=status.HTTP_201_CREATED)
        else:
            print('invalid')
            return Response(image_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PresignedURLView(APIView):
    def get(self, request, *args, **kwargs):
        s3_client = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                                        aws_session_token=os.getenv('AWS_SESSION_TOKEN'))
        bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')

        # List all the files in the specified S3 bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        files = response.get('Contents', [])

        # Generate a presigned URL for each file
        presigned_urls = []
        for file in files:
            key = file['Key']
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=3600  # or any duration you want
            )
            presigned_urls.append({'file_name': key, 'presigned_url': presigned_url})

        return Response(presigned_urls)