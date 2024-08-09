from .s3_objects import delete_file, generate_presigned_url, list_files, upload_file
from .s3_exceptions import UserProfilePictureNotFound

def get_user_profile_picture_url(user_id):
    file_path = f'users/{user_id}/profile_picture/'
    files = list_files(file_path)
    if not files:
        raise UserProfilePictureNotFound
    return generate_presigned_url(files[0]['Key'])

def set_user_profile_picture(user_id, file_content, file_name):
    file_path = f'users/{user_id}/profile_picture/'
    files = list_files(file_path)
    
    if files:
        delete_file(files[0]['Key'])

    file_name = file_path + file_name
    upload_file(file_content, file_name)