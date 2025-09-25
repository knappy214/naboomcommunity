from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from home.views import serve_image

from .api import api_router
from api.urls import api_urlpatterns
try:
    from panic.api import api_router as panic_api_router
except Exception:  # pragma: no cover - panic app optional in test settings
    panic_api_router = None

urlpatterns = [
    # Wagtail admin (replaces Django admin)
    path("admin/", include(wagtailadmin_urls)),
    
    # Django admin (moved to /django-admin/ to avoid conflicts)
    path("django-admin/", admin.site.urls),

    # Wagtail API v2 content and app endpoints (includes i18n support)
    path(
        "api/v2/",
        include(
            (
                api_router.get_urlpatterns()
                + (panic_api_router.get_urlpatterns() if panic_api_router else [])
                + api_urlpatterns,
                "wagtailapi",
            ),
            namespace="wagtailapi",
        ),
    ),
    
    # Our custom app APIs (Django REST Framework)
    path("api/", include(api_urlpatterns)),
    path("api/v1/", include(api_urlpatterns)),
    *( [path("panic/", include("panic.urls"))] if panic_api_router else [] ),

    # OpenAPI for our custom endpoints
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),

    # Language switching
    path("i18n/", include("django.conf.urls.i18n")),

    # Custom app views
    path("", include("home.urls")),

    # Custom image serving for S3
    re_path(r'^images/([^/]*)/(\d*)/([^/]*)/[^/]*$', serve_image, name='wagtailimages_serve'),

    # Wagtail catch-all - must be last
    re_path(r"^", include(wagtail_urls)),
]

# Serve static and media files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

