import boto3
import os

sts_client = boto3.client('sts')

def assume_role(role_arn, session_name):
    response = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name
    )
    return response['Credentials']

account_id = os.getenv('AWS_ACCOUNT_ID')
credentials = assume_role(
    role_arn=f'arn:aws:iam::{account_id}:role/S3AccessRole',
    session_name='SimpleboxBackendSession'
)

client = boto3.client(
    's3',
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken']
)

bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
