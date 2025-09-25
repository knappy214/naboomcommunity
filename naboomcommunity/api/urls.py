from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .auth_views import (
    EmailTokenObtainPairView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
)
from .user_profile_views import (
    AvatarDeleteView,
    AvatarUploadView,
    UserBasicInfoUpdateView,
    UserGroupListView,
    UserGroupMembershipDetailView,
    UserGroupMembershipListView,
    UserPasswordChangeView,
    UserProfileDetailView,
    UserProfileUpdateView,
    UserRoleListView,
    avatar_info,
    join_group,
    leave_group,
    set_avatar_from_existing,
    user_profile_stats,
)
from .viewsets import health

router = DefaultRouter()  # no custom viewsets; pages served via Wagtail API v2

# Expose API endpoints as a simple pattern list so they can be included
# under multiple prefixes (e.g. /api/, /api/v1/, /api/v2/).
api_urlpatterns = [
    path("", include(router.urls)),

    # JWT auth
    path("auth/jwt/create/", EmailTokenObtainPairView.as_view(), name="jwt-create"),
    path("auth/jwt/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
    path("auth/jwt/verify/", TokenVerifyView.as_view(), name="jwt-verify"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),

    path("health/", health),

    # User Profile endpoints
    path("user-profile/", UserProfileDetailView.as_view(), name="user-profile-detail"),
    path("user-profile/update/", UserProfileUpdateView.as_view(), name="user-profile-update"),
    path("user-profile/basic-info/", UserBasicInfoUpdateView.as_view(), name="user-profile-basic-info"),
    path("user-profile/change-password/", UserPasswordChangeView.as_view(), name="user-profile-change-password"),
    path("user-profile/stats/", user_profile_stats, name="user-profile-stats"),
    path("user-profile/join-group/", join_group, name="user-profile-join-group"),
    path("user-profile/leave-group/", leave_group, name="user-profile-leave-group"),
    path("user-profile/group-memberships/", UserGroupMembershipListView.as_view(), name="user-group-membership-list"),
    path(
        "user-profile/group-memberships/<int:pk>/",
        UserGroupMembershipDetailView.as_view(),
        name="user-group-membership-detail",
    ),

    # Avatar endpoints
    path("user-profile/avatar/upload/", AvatarUploadView.as_view(), name="user-profile-avatar-upload"),
    path("user-profile/avatar/delete/", AvatarDeleteView.as_view(), name="user-profile-avatar-delete"),
    path("user-profile/avatar/info/", avatar_info, name="user-profile-avatar-info"),
    path(
        "user-profile/avatar/set-existing/",
        set_avatar_from_existing,
        name="user-profile-avatar-set-existing",
    ),

    # User Groups and Roles
    path("user-groups/", UserGroupListView.as_view(), name="user-group-list"),
    path("user-roles/", UserRoleListView.as_view(), name="user-role-list"),
    path("community/", include("communityhub.api.urls")),
]

# Maintain the original name for backwards compatibility
urlpatterns = api_urlpatterns
