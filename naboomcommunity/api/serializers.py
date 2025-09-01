from rest_framework import serializers
from wagtail.models import Page


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = [
            "id",
            "title",
            "slug",
            "url",
            "first_published_at",
            "latest_revision_created_at",
        ]
