from __future__ import annotations

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import BaseAPIViewSet

from .models import Incident, PatrolAlert, Responder
from .serializers import IncidentSerializer, PatrolAlertSerializer, ResponderSerializer


class IncidentAPIViewSet(BaseAPIViewSet):
    name = "panic-incidents"
    model = Incident
    serializer_class = IncidentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def authenticate_user(self, request) -> bool:
        """Authenticate request using JWT token."""
        authenticator = JWTAuthentication()
        try:
            user_auth = authenticator.authenticate(request)
            if user_auth is None:
                return False
            request.user, _ = user_auth
            return True
        except Exception:
            return False

    def get_queryset(self):
        return (
            Incident.objects.select_related("client")
            .prefetch_related("events")
            .order_by("-created_at")
        )

    def listing_view(self, request):
        if not self.authenticate_user(request):
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
            
        queryset = self.get_queryset()
        status = request.GET.get("status")
        province = request.GET.get("province")
        if status:
            queryset = queryset.filter(status=status)
        if province:
            queryset = queryset.filter(province=province)

        try:
            limit = min(int(request.GET.get("limit", 50)), 200)
        except (TypeError, ValueError):
            limit = 50
        items = [self.serializer_class(instance).data for instance in queryset[:limit]]
        return JsonResponse({"meta": {"total_count": queryset.count()}, "items": items})

    def detail_view(self, request, pk):
        if not self.authenticate_user(request):
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
            
        incident = self.get_queryset().filter(pk=pk).first()
        if not incident:
            return JsonResponse({"detail": "not found"}, status=404)
        return JsonResponse(self.serializer_class(incident).data)


class ResponderAPIViewSet(BaseAPIViewSet):
    name = "panic-responders"
    model = Responder
    serializer_class = ResponderSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def authenticate_user(self, request) -> bool:
        """Authenticate request using JWT token."""
        authenticator = JWTAuthentication()
        try:
            user_auth = authenticator.authenticate(request)
            if user_auth is None:
                return False
            request.user, _ = user_auth
            return True
        except Exception:
            return False

    def get_queryset(self):
        queryset = Responder.objects.filter(is_active=True)
        province = self.request.GET.get("province") if hasattr(self, "request") else None
        if province:
            queryset = queryset.filter(province=province)
        return queryset.order_by("full_name")

    def listing_view(self, request):
        if not self.authenticate_user(request):
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
        
        self.request = request
        queryset = self.get_queryset()
        items = [self.serializer_class(instance).data for instance in queryset]
        return JsonResponse({"meta": {"total_count": len(items)}, "items": items})

    def detail_view(self, request, pk):
        if not self.authenticate_user(request):
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
            
        responder = Responder.objects.filter(pk=pk, is_active=True).first()
        if not responder:
            return JsonResponse({"detail": "not found"}, status=404)
        return JsonResponse(self.serializer_class(responder).data)


class PatrolAlertAPIViewSet(BaseAPIViewSet):
    name = "panic-alerts"
    model = PatrolAlert
    serializer_class = PatrolAlertSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PatrolAlert.objects.select_related("waypoint").order_by("-created_at")
        shift_id = self.request.GET.get("shift") if hasattr(self, "request") else None
        if shift_id:
            queryset = queryset.filter(shift_id=shift_id)
        return queryset

    def listing_view(self, request):
        self.request = request
        queryset = self.get_queryset()
        try:
            limit = min(int(request.GET.get("limit", 100)), 200)
        except (TypeError, ValueError):
            limit = 100
        items = [self.serializer_class(instance).data for instance in queryset[:limit]]
        return JsonResponse({"meta": {"total_count": queryset.count()}, "items": items})

    def detail_view(self, request, pk):
        alert = PatrolAlert.objects.select_related("waypoint").filter(pk=pk).first()
        if not alert:
            return JsonResponse({"detail": "not found"}, status=404)
        return JsonResponse(self.serializer_class(alert).data)


api_router = WagtailAPIRouter("panic")
api_router.register_endpoint("incidents", IncidentAPIViewSet)
api_router.register_endpoint("responders", ResponderAPIViewSet)
api_router.register_endpoint("alerts", PatrolAlertAPIViewSet)
