"""
Management command to fix image URLs for S3 storage.
"""
from django.core.management.base import BaseCommand
from wagtail.images.models import Image
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix image URLs for S3 storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        images = Image.objects.all()
        self.stdout.write(f'Found {images.count()} images to check')
        
        fixed_count = 0
        error_count = 0
        
        for image in images:
            try:
                self.stdout.write(f'Processing: {image.title}')
                
                # Check if the image file exists in storage
                if image.file and image.file.storage.exists(image.file.name):
                    self.stdout.write(f'  ✅ File exists in storage: {image.file.name}')
                    self.stdout.write(f'  📍 File URL: {image.file.url}')
                    
                    # Check if the URL is accessible
                    try:
                        import requests
                        response = requests.head(image.file.url, timeout=5)
                        if response.status_code == 200:
                            self.stdout.write(f'  ✅ URL accessible: {response.status_code}')
                        else:
                            self.stdout.write(f'  ❌ URL not accessible: {response.status_code}')
                    except Exception as e:
                        self.stdout.write(f'  ⚠️  URL check failed: {e}')
                    
                    # Try to get a rendition
                    try:
                        rendition = image.get_rendition('max-100x100')
                        self.stdout.write(f'  📍 Rendition URL: {rendition.url}')
                        
                        if rendition.file.storage.exists(rendition.file.name):
                            self.stdout.write(f'  ✅ Rendition exists in storage')
                        else:
                            self.stdout.write(f'  ❌ Rendition not in storage')
                            
                    except Exception as e:
                        self.stdout.write(f'  ❌ Rendition error: {e}')
                        error_count += 1
                else:
                    self.stdout.write(f'  ❌ File not found in storage')
                    error_count += 1
                    
                self.stdout.write('---')
                    
            except Exception as e:
                self.stdout.write(f'  ❌ Error processing {image.title}: {e}')
                error_count += 1
        
        self.stdout.write(f'\n✅ Checked {images.count()} images')
        if error_count > 0:
            self.stdout.write(f'❌ {error_count} images had errors')
