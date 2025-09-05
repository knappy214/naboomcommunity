"""
Custom views for the home app.
"""
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from wagtail.images.models import Image
from wagtail.images.views.serve import serve as wagtail_serve
import logging

logger = logging.getLogger(__name__)


def test_css(request):
    """Test CSS view."""
    return HttpResponse("CSS test page")


def home_view(request):
    """Home view."""
    return render(request, 'home/home.html')


@never_cache
@require_http_methods(["GET"])
def serve_image(request, signature, image_id, filter_spec):
    """
    Custom image serving view that handles S3 images properly.
    """
    try:
        # Get the image
        image = Image.objects.get(id=image_id)
        
        # Get the rendition
        rendition = image.get_rendition(filter_spec)
        
        # Check if the rendition file exists in S3
        if rendition.file and rendition.file.storage.exists(rendition.file.name):
            # Serve the file directly from S3
            file = rendition.file
            response = HttpResponse(
                file.read(),
                content_type=file.content_type or 'image/jpeg'
            )
            response['Content-Disposition'] = f'inline; filename="{file.name}"'
            return response
        else:
            # Fallback to Wagtail's default serving
            return wagtail_serve(request, signature, image_id, filter_spec)
            
    except Image.DoesNotExist:
        raise Http404("Image not found")
    except Exception as e:
        logger.error(f"Error serving image {image_id}: {e}")
        raise Http404("Error serving image")