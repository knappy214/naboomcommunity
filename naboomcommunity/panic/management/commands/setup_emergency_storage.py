"""
Django management command to setup emergency storage buckets and folders.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Setup emergency storage buckets and folder structure in MinIO'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bucket-name',
            type=str,
            default=getattr(settings, 'EMERGENCY_STORAGE_BUCKET_NAME', 'naboom-emergency-media'),
            help='Name of the emergency storage bucket'
        )
        parser.add_argument(
            '--endpoint-url',
            type=str,
            default=getattr(settings, 'EMERGENCY_STORAGE_ENDPOINT_URL', 'https://s3.naboomneighbornet.net.za'),
            help='MinIO endpoint URL'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if bucket exists'
        )

    def handle(self, *args, **options):
        bucket_name = options['bucket_name']
        endpoint_url = options['endpoint_url']
        force = options['force']

        self.stdout.write(
            self.style.SUCCESS(f'Setting up emergency storage bucket: {bucket_name}')
        )

        try:
            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            # Check if bucket exists
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                if not force:
                    self.stdout.write(
                        self.style.WARNING(f'Bucket {bucket_name} already exists. Use --force to recreate.')
                    )
                    return
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Bucket {bucket_name} exists. Recreating...')
                    )
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    # Bucket doesn't exist, create it
                    self.stdout.write(f'Creating bucket: {bucket_name}')
                    s3_client.create_bucket(Bucket=bucket_name)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created bucket: {bucket_name}')
                    )
                else:
                    raise

            # Create folder structure
            folders = [
                'emergency/media/',
                'emergency/location/',
                'emergency/medical/',
                'emergency/notifications/',
                'emergency/backup/',
                'emergency/temp/',
            ]

            for folder in folders:
                try:
                    # Create folder by uploading an empty object
                    s3_client.put_object(
                        Bucket=bucket_name,
                        Key=folder,
                        Body=b'',
                        ContentType='application/x-directory'
                    )
                    self.stdout.write(f'✓ Created folder: {folder}')
                except ClientError as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to create folder {folder}: {str(e)}')
                    )

            # Set bucket policy for emergency files
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "EmergencyFilesPolicy",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{settings.AWS_ACCESS_KEY_ID}:root"
                        },
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject"
                        ],
                        "Resource": f"arn:aws:s3:::{bucket_name}/emergency/*"
                    },
                    {
                        "Sid": "DenyPublicAccess",
                        "Effect": "Deny",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/emergency/*",
                        "Condition": {
                            "StringNotEquals": {
                                "aws:PrincipalServiceName": "naboom-emergency-service"
                            }
                        }
                    }
                ]
            }

            try:
                s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=str(bucket_policy).replace("'", '"')
                )
                self.stdout.write('✓ Applied emergency storage policy')
            except ClientError as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Could not apply bucket policy: {str(e)}')
                )

            # Test storage access
            test_key = 'emergency/test/connection_test.txt'
            try:
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=test_key,
                    Body=b'Emergency storage connection test',
                    ContentType='text/plain'
                )
                
                # Verify the object was created
                response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
                if response['Body'].read() == b'Emergency storage connection test':
                    self.stdout.write('✓ Storage access test successful')
                else:
                    self.stdout.write(
                        self.style.ERROR('✗ Storage access test failed')
                    )
                
                # Clean up test object
                s3_client.delete_object(Bucket=bucket_name, Key=test_key)
                
            except ClientError as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Storage access test failed: {str(e)}')
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Emergency storage setup completed successfully!\n'
                    f'  Bucket: {bucket_name}\n'
                    f'  Endpoint: {endpoint_url}\n'
                    f'  Folders created: {len(folders)}'
                )
            )

        except Exception as e:
            raise CommandError(f'Emergency storage setup failed: {str(e)}')
