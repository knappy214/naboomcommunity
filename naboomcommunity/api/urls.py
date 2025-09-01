from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .auth_views import (
    EmailTokenObtainPairView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
)
from .viewsets import health

router = DefaultRouter()  # no custom viewsets; pages served via Wagtail API v2

urlpatterns = [
    path(
        "",
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
                path("health/", health),
            ]
        ),
    ),
]
