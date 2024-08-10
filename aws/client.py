import boto3
import os
from datetime import datetime, timedelta

class AWSClientManager:
    def __init__(self, s3_role_arn, s3_session_name, sqs_role_arn, sqs_session_name, region_name):
        self.s3_role_arn = s3_role_arn
        self.s3_session_name = s3_session_name
        self.sqs_role_arn = sqs_role_arn
        self.sqs_session_name = sqs_session_name
        self.region_name = region_name
        self.s3_credentials = None
        self.s3_expiration = None
        self.sqs_credentials = None
        self.sqs_expiration = None
        self.s3_client = None
        self.sqs_client = None

        # Initialize STS client
        self.sts_client = boto3.client('sts', region_name=self.region_name)

        # Initial credential refresh
        self.refresh_s3_credentials()
        self.refresh_sqs_credentials()

    def refresh_s3_credentials(self):
        try:
            response = self.sts_client.assume_role(
                RoleArn=self.s3_role_arn,
                RoleSessionName=self.s3_session_name
            )
            self.s3_credentials = response['Credentials']
            self.s3_expiration = self.s3_credentials['Expiration']

            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.s3_credentials['AccessKeyId'],
                aws_secret_access_key=self.s3_credentials['SecretAccessKey'],
                aws_session_token=self.s3_credentials['SessionToken'],
                region_name=self.region_name
            )
        except Exception as e:
            print(f"Failed to refresh S3 credentials: {str(e)}")
            raise

    def refresh_sqs_credentials(self):
        try:
            response = self.sts_client.assume_role(
                RoleArn=self.sqs_role_arn,
                RoleSessionName=self.sqs_session_name
            )
            self.sqs_credentials = response['Credentials']
            self.sqs_expiration = self.sqs_credentials['Expiration']

            self.sqs_client = boto3.client(
                'sqs',
                aws_access_key_id=self.sqs_credentials['AccessKeyId'],
                aws_secret_access_key=self.sqs_credentials['SecretAccessKey'],
                aws_session_token=self.sqs_credentials['SessionToken'],
                region_name=self.region_name
            )
        except Exception as e:
            print(f"Failed to refresh SQS credentials: {str(e)}")
            raise

    def is_s3_credentials_expired(self):
        return datetime.now() + timedelta(minutes=5) >= self.s3_expiration

    def is_sqs_credentials_expired(self):
        return datetime.now() + timedelta(minutes=5) >= self.sqs_expiration

    def get_s3_client(self):
        if self.is_s3_credentials_expired():
            self.refresh_s3_credentials()
        return self.s3_client

    def get_sqs_client(self):
        if self.is_sqs_credentials_expired():
            self.refresh_sqs_credentials()
        return self.sqs_client

    def send_sqs_message(self, queue_url, message_body, message_attributes=None):
        sqs_client = self.get_sqs_client()
        try:
            response = sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=message_body,
                MessageAttributes=message_attributes or {}
            )
            return response
        except Exception as e:
            print(f"Failed to send SQS message: {str(e)}")
            raise

account_id = os.getenv('AWS_ACCOUNT_ID')
region_name = os.getenv('AWS_REGION')
s3_role_arn = f'arn:aws:iam::{account_id}:role/S3AccessRole'
s3_session_name = 'S3BackendSession'
sqs_role_arn = f'arn:aws:iam::{account_id}:role/SQSAccessRole'
sqs_session_name = 'SQSBackendSession'
bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
queue_url = os.getenv('AWS_SQS_QUEUE_URL')

aws_manager = AWSClientManager(s3_role_arn, s3_session_name, sqs_role_arn, sqs_session_name, region_name)
