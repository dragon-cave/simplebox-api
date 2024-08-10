import boto3
import os
from datetime import datetime, timedelta

class AWSClientManager:
    def __init__(self, role_arn, session_name):
        self.sts_client = None
        self.role_arn = role_arn
        self.session_name = session_name
        self.credentials = None
        self.expiration = None
        self.s3_client = None
        self.sqs_client = None
        self.refresh_credentials()

    def refresh_credentials(self):
        response = self.sts_client.assume_role(
            RoleArn=self.role_arn,
            RoleSessionName=self.session_name
        )
        self.credentials = response['Credentials']
        self.expiration = self.credentials['Expiration']

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.credentials['AccessKeyId'],
            aws_secret_access_key=self.credentials['SecretAccessKey'],
            aws_session_token=self.credentials['SessionToken']
        )

        self.sqs_client = boto3.client(
            'sqs',
            aws_access_key_id=self.credentials['AccessKeyId'],
            aws_secret_access_key=self.credentials['SecretAccessKey'],
            aws_session_token=self.credentials['SessionToken']
        )

    def is_credentials_expired(self):
        return datetime.now() + timedelta(minutes=5) >= self.expiration

    def get_s3_client(self):
        if self.is_credentials_expired():
            self.refresh_credentials()
        return self.s3_client

    def get_sqs_client(self):
        if self.is_credentials_expired():
            self.refresh_credentials()
        return self.sqs_client

    def send_sqs_message(self, queue_url, message_body, message_attributes=None):
        sqs_client = self.get_sqs_client()
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body,
            MessageAttributes=message_attributes or {}
        )
        return response

account_id = os.getenv('AWS_ACCOUNT_ID')
role_arn = f'arn:aws:iam::{account_id}:role/S3AccessRole'
session_name = 'SimpleboxBackendSession'
bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')
queue_url = os.getenv('AWS_SQS_QUEUE_URL')

aws_manager = AWSClientManager(role_arn, session_name)