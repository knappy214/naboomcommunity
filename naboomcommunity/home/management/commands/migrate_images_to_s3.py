"""
Management command to migrate existing Wagtail images to S3 storage.
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from wagtail.images.models import Image
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Migrate existing Wagtail images to S3 storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get the S3 storage backend
        from naboomcommunity.custom_storages import MediaStorage
        s3_storage = MediaStorage()
        
        images = Image.objects.all()
        self.stdout.write(f'Found {images.count()} images to check')
        
        migrated_count = 0
        error_count = 0
        
        for image in images:
            try:
                # Check if image file exists locally
                if image.file and hasattr(image.file, 'path'):
                    local_path = image.file.path
                    if os.path.exists(local_path):
                        self.stdout.write(f'Processing: {image.title}')
                        
                        if not dry_run:
                            # Read the file content
                            with open(local_path, 'rb') as f:
                                file_content = f.read()
                            
                            # Create new file in S3
                            file_name = os.path.basename(local_path)
                            s3_file = ContentFile(file_content, name=file_name)
                            
                            # Save to S3
                            image.file.save(file_name, s3_file, save=True)
                            
                            # Verify S3 upload
                            if s3_storage.exists(image.file.name):
                                self.stdout.write(f'  ✅ Migrated to S3: {image.file.url}')
                                migrated_count += 1
                            else:
                                self.stdout.write(f'  ❌ Failed to verify S3 upload')
                                error_count += 1
                        else:
                            self.stdout.write(f'  [DRY RUN] Would migrate: {image.title}')
                            migrated_count += 1
                    else:
                        self.stdout.write(f'  ⚠️  Local file not found: {image.title}')
                else:
                    self.stdout.write(f'  ℹ️  No local file path: {image.title}')
                    
            except Exception as e:
                self.stdout.write(f'  ❌ Error processing {image.title}: {e}')
                error_count += 1
        
        if dry_run:
            self.stdout.write(f'\n[DRY RUN] Would migrate {migrated_count} images')
        else:
            self.stdout.write(f'\n✅ Successfully migrated {migrated_count} images')
            if error_count > 0:
                self.stdout.write(f'❌ {error_count} images had errors')
