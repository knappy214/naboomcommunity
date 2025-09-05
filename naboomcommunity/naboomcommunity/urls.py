from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.images.views.serve import serve
from home.views import serve_image

from .api import api_router

urlpatterns = [
    # Wagtail admin (replaces Django admin)
    path("admin/", include(wagtailadmin_urls)),
    
    # Django admin (moved to /django-admin/ to avoid conflicts)
    path("django-admin/", admin.site.urls),

    # Wagtail API v2 (content)
    path("api/v2/", api_router.urls),

    # Our custom app APIs (auth, health, etc.)
    path("api/", include("api.urls")),

    # OpenAPI for our custom endpoints
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),

    # Language switching
    path("i18n/", include("django.conf.urls.i18n")),

    # Custom app views
    path("", include("home.urls")),

    # Custom image serving for S3
    re_path(r'^images/([^/]*)/(\d*)/([^/]*)/[^/]*$', serve_image, name='wagtailimages_serve'),

    # Keep below API routes
    re_path(r"^", include(wagtail_urls)),
]

# Serve static and media files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

