import os
from .s3 import bucket_name, client

def list_files(prefix=''):
    response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    return response.get('Contents', [])

def generate_presigned_url(file_name, expiration=3600):
    return client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': file_name},
        ExpiresIn=expiration
    )

def delete_file(file_name):
    client.delete_object(Bucket=bucket_name, Key=file_name)

def upload_file(file, file_name):
    client.upload_fileobj(file, bucket_name, file_name)