from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import PageViewSet, health
from .auth_views import (
    RegisterView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailTokenObtainPairView,
)
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

router = DefaultRouter()
router.register(r"pages", PageViewSet, basename="pages")

urlpatterns = [
    path(
        "v1/",
        include(
            [
                path("", include(router.urls)),
                path("auth/jwt/create", EmailTokenObtainPairView.as_view()),
                path("auth/jwt/refresh", TokenRefreshView.as_view()),
                path("auth/jwt/verify", TokenVerifyView.as_view()),
                path("auth/register", RegisterView.as_view()),
                path("auth/password-reset", PasswordResetRequestView.as_view()),
                path(
                    "auth/password-reset/confirm",
                    PasswordResetConfirmView.as_view(),
                ),
            ]
        ),
    ),
    path("health/", health),
]
