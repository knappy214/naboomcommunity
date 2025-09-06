from django.urls import path
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from wagtail.contrib.redirects.api import RedirectsAPIViewSet
from .test_viewset import test_user_profiles

# Create the router. "wagtailapi" is the URL namespace
api_router = WagtailAPIRouter('wagtailapi')

# Register the endpoints
api_router.register_endpoint('pages', PagesAPIViewSet)
api_router.register_endpoint('images', ImagesAPIViewSet)
api_router.register_endpoint('documents', DocumentsAPIViewSet)
api_router.register_endpoint('redirects', RedirectsAPIViewSet)

# Create custom URL patterns that will be included with the router
custom_api_patterns = [
    path('user-profiles/', test_user_profiles, name='user-profiles'),
]

# Export the router and custom patterns separately.
# The URLs file will handle combining them properly.
