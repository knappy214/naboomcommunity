from rest_framework import viewsets, permissions
from rest_framework.response import Response
from wagtail.models import Page
from .serializers import PageSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


class PageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Page.objects.live().public()
    serializer_class = PageSerializer
    permission_classes = [permissions.AllowAny]


@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request):
    return Response({"status": "ok"})
