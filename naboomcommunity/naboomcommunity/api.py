from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication


class AuthenticatedPagesAPIViewSet(PagesAPIViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class AuthenticatedImagesAPIViewSet(ImagesAPIViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class AuthenticatedDocumentsAPIViewSet(DocumentsAPIViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


api_router = WagtailAPIRouter("wagtailapi")
api_router.register_endpoint("pages", AuthenticatedPagesAPIViewSet)
api_router.register_endpoint("images", AuthenticatedImagesAPIViewSet)
api_router.register_endpoint("documents", AuthenticatedDocumentsAPIViewSet)
