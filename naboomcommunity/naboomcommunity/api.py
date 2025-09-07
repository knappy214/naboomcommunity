from django.urls import path
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.contrib.redirects.api import RedirectsAPIViewSet
from rest_framework.permissions import AllowAny

from .wagtail_api_views import (
    UserGroupAPIViewSet,
    UserGroupMembershipAPIViewSet,
    UserProfileAPIViewSet,
    UserRoleAPIViewSet,
)


# Make the Wagtail API endpoints publicly accessible. Other DRF views
# remain protected via the global IsAuthenticated permission class.


class PublicPagesAPIViewSet(PagesAPIViewSet):
    permission_classes = [AllowAny]


class PublicImagesAPIViewSet(ImagesAPIViewSet):
    permission_classes = [AllowAny]


class PublicDocumentsAPIViewSet(DocumentsAPIViewSet):
    permission_classes = [AllowAny]


class PublicRedirectsAPIViewSet(RedirectsAPIViewSet):
    permission_classes = [AllowAny]


# Create the router. "wagtailapi" is the URL namespace
api_router = WagtailAPIRouter("wagtailapi")

# Register the endpoints
api_router.register_endpoint("pages", PublicPagesAPIViewSet)
api_router.register_endpoint("images", PublicImagesAPIViewSet)
api_router.register_endpoint("documents", PublicDocumentsAPIViewSet)
api_router.register_endpoint("redirects", PublicRedirectsAPIViewSet)
api_router.register_endpoint("user-profiles", UserProfileAPIViewSet)
api_router.register_endpoint("user-groups", UserGroupAPIViewSet)
api_router.register_endpoint("user-roles", UserRoleAPIViewSet)
api_router.register_endpoint("user-group-memberships", UserGroupMembershipAPIViewSet)

# Export the router for use in the project's URL configuration
