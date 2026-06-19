"""
apps/users/presentation/urls.py
URL routing for the user-service.

Route map:
  /api/v1/auth/register/           → RegisterView
  /api/v1/auth/login/              → LoginView (JWT)
  /api/v1/auth/logout/             → LogoutView
  /api/v1/auth/token/refresh/      → TokenRefreshView
  /api/v1/auth/verify-email/       → VerifyEmailView

  /api/v1/users/                   → UserViewSet (Staff/Admin)
  /api/v1/users/me/                → UserProfileView (owner)
  /api/v1/users/me/change-password/→ ChangePasswordView
  /api/v1/users/me/addresses/      → AddressListCreateView
  /api/v1/users/me/addresses/<id>/ → AddressDetailView

  /api/v1/internal/users/<id>/     → InternalUserDetailView (service-to-service)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.presentation.views import (
    RegisterView,
    LoginView,
    LogoutView,
    VerifyEmailView,
    UserProfileView,
    ChangePasswordView,
    AddressListCreateView,
    AddressDetailView,
    UserViewSet,
    InternalUserDetailView,
)

# ── Admin/Staff router ────────────────────────────────────────────────────────
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    # ── Authentication ────────────────────────────────────────────────────────
    path("api/v1/auth/register/",        RegisterView.as_view(),      name="auth-register"),
    path("api/v1/auth/login/",           LoginView.as_view(),         name="auth-login"),
    path("api/v1/auth/logout/",          LogoutView.as_view(),        name="auth-logout"),
    path("api/v1/auth/token/refresh/",   TokenRefreshView.as_view(),  name="token-refresh"),
    path("api/v1/auth/verify-email/",    VerifyEmailView.as_view(),   name="auth-verify-email"),

    # ── Own profile ───────────────────────────────────────────────────────────
    path("api/v1/users/me/",                          UserProfileView.as_view(),     name="user-profile"),
    path("api/v1/users/me/change-password/",          ChangePasswordView.as_view(),  name="change-password"),
    path("api/v1/users/me/addresses/",                AddressListCreateView.as_view(), name="address-list"),
    path("api/v1/users/me/addresses/<uuid:pk>/",      AddressDetailView.as_view(),   name="address-detail"),

    # ── Admin/Staff CRUD (router) ─────────────────────────────────────────────
    path("api/v1/", include(router.urls)),

    # ── Internal service-to-service ───────────────────────────────────────────
    path("api/v1/internal/users/<uuid:id>/", InternalUserDetailView.as_view(), name="internal-user-detail"),
]
