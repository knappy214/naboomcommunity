"""
Management command to setup MinIO buckets for the application.
"""
import boto3
from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup MinIO buckets for static and media files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bucket-name',
            type=str,
            default=settings.AWS_STORAGE_BUCKET_NAME,
            help='Name of the bucket to create'
        )

    def handle(self, *args, **options):
        bucket_name = options['bucket_name']
        
        # Create S3 client for MinIO
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            use_ssl=True,  # Your endpoint uses HTTPS
            verify=True    # Verify SSL certificates
        )

        try:
            # Check if bucket exists
            s3_client.head_bucket(Bucket=bucket_name)
            self.stdout.write(
                self.style.SUCCESS(f'Bucket "{bucket_name}" already exists')
            )
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                # Bucket doesn't exist, create it
                try:
                    s3_client.create_bucket(Bucket=bucket_name)
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully created bucket "{bucket_name}"')
                    )
                except ClientError as create_error:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating bucket: {create_error}')
                    )
                    return
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error checking bucket: {e}')
                )
                return

        # Create folder structure
        folders = ['static/', 'media/', 'documents/']
        for folder in folders:
            try:
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=folder,
                    Body=b''
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created folder "{folder}" in bucket "{bucket_name}"')
                )
            except ClientError as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not create folder "{folder}": {e}')
                )

        self.stdout.write(
            self.style.SUCCESS('MinIO setup completed successfully!')
        )
