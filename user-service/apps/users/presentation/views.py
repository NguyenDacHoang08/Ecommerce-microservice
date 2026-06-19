"""
apps/users/presentation/views.py
API Views – Presentation layer (thin controllers).

RBAC enforcement via permission classes:
  /auth/*       → AllowAny (register/login)
  /users/me/    → IsAuthenticated (owner)
  /users/       → IsStaffOrAdmin (list) | IsAdmin (CRUD)
  /internal/*   → InternalServicePermission
"""
from __future__ import annotations

import logging

from django.db import transaction
from rest_framework import generics, viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend

from apps.users.domain.models import User, Address, Role, UserStatus
from apps.users.presentation.serializers import (
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    AdminUserSerializer,
    ChangePasswordSerializer,
    AddressSerializer,
    CustomTokenObtainPairSerializer,
)
from apps.users.application.services import UserApplicationService
from apps.core.permissions import (
    IsAdmin,
    IsStaffOrAdmin,
    IsOwnerOrAdmin,
    InternalServicePermission,
)

logger = logging.getLogger(__name__)


# ─── Auth Views ───────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Open endpoint – anyone can self-register as a customer.
    """
    serializer_class   = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()

        # Side-effect: send verification email (async in prod)
        UserApplicationService.send_verification_email(user)

        logger.info("New user registered: email=%s id=%s", user.email, user.id)
        return Response(
            {"message": "Registration successful. Please verify your email."},
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Returns: { access, refresh, user: {...} }
    JWT payload includes: user_id, email, role, username, is_staff
    """
    serializer_class   = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the refresh token – requires token_blacklist app.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("User logged out: user=%s", request.user.id)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    """
    GET /api/v1/auth/verify-email/?token=<token>
    Domain action: verify_email() enforces idempotency.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = request.query_params.get("token")
        user  = UserApplicationService.verify_email_token(token)
        if not user:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user.verify_email()   # domain method
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Email verified successfully."})


# ─── Own Profile Views ────────────────────────────────────────────────────────

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/users/me/  → full profile (UserSerializer)
    PATCH /api/v1/users/me/ → update name/phone/avatar (UserUpdateSerializer)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    POST /api/v1/users/me/change-password/
    Validates old password domain rule, then updates.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password", "updated_at"])

        logger.info("Password changed: user=%s", request.user.id)
        return Response({"message": "Password changed successfully."})


# ─── Address Views ────────────────────────────────────────────────────────────

class AddressListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/users/me/addresses/
    POST /api/v1/users/me/addresses/
    """
    serializer_class   = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PATCH/DELETE /api/v1/users/me/addresses/<id>/
    Object-level: only owner can access their own addresses.
    """
    serializer_class   = AddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return self.request.user.addresses.all()


# ─── Admin: UserViewSet ───────────────────────────────────────────────────────

class UserViewSet(viewsets.ModelViewSet):
    """
    Admin / Staff ViewSet for user management.
    GET  /api/v1/users/         → Staff + Admin: list all users
    POST /api/v1/users/         → Admin only: create user with any role
    GET  /api/v1/users/<id>/    → Staff + Admin
    PATCH /api/v1/users/<id>/   → Admin only
    DELETE /api/v1/users/<id>/  → Admin only (soft delete)

    Extra actions:
      POST /api/v1/users/<id>/suspend/  → Admin only
      POST /api/v1/users/<id>/activate/ → Admin only
    """
    queryset         = User.objects.select_related().prefetch_related("addresses")
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["role", "status", "is_active", "email_verified"]
    search_fields    = ["email", "username", "full_name", "phone"]
    ordering_fields  = ["created_at", "full_name", "email", "login_count"]
    ordering         = ["-created_at"]

    def get_serializer_class(self):
        # Staff get read-only public view; admins get full admin view
        if self.request.user and self.request.user.is_admin():
            return AdminUserSerializer
        return UserSerializer

    def get_permissions(self):
        """Role-based permission dispatch."""
        if self.action in ("list", "retrieve"):
            # Staff and Admin can read
            return [IsStaffOrAdmin()]
        if self.action in ("create", "update", "partial_update", "destroy", "suspend", "activate"):
            # Only Admin can mutate
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    @transaction.atomic
    def perform_destroy(self, instance):
        """Hard delete: delete user from database."""
        if instance.is_admin():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin accounts cannot be deleted via API.")
        instance.delete()
        logger.warning("User permanently deleted: id=%s by admin=%s", instance.id, self.request.user.id)

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin], url_path="suspend")
    def suspend(self, request, pk=None):
        """
        POST /api/v1/users/<id>/suspend/
        Domain action: enforces Admin cannot be suspended.
        """
        user = self.get_object()
        reason = request.data.get("reason", "")
        try:
            user.suspend(reason=reason)
            logger.warning("User suspended: id=%s by admin=%s", user.id, request.user.id)
        except (ValueError, PermissionError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": f"User {user.email} has been suspended."})

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin], url_path="activate")
    def activate(self, request, pk=None):
        """POST /api/v1/users/<id>/activate/"""
        user = self.get_object()
        try:
            user.activate()
            logger.info("User activated: id=%s by admin=%s", user.id, request.user.id)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": f"User {user.email} is now active."})

    @action(detail=False, methods=["get"], permission_classes=[IsStaffOrAdmin], url_path="by-role/(?P<role>[^/.]+)")
    def by_role(self, request, role=None):
        """GET /api/v1/users/by-role/<role>/ – filter users by role."""
        valid_roles = [r.value for r in Role]
        if role not in valid_roles:
            return Response(
                {"error": f"Invalid role. Choose from: {valid_roles}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(role=role)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ─── Internal Service-to-Service API ─────────────────────────────────────────

class InternalUserDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/internal/users/<id>/
    Called by order-service, cart-service etc. to validate user.
    Protected by X-Internal-Token header (not JWT).
    """
    serializer_class = UserSerializer
    queryset         = User.objects.all()
    lookup_field     = "id"

    def get_permissions(self):
        return [InternalServicePermission()]
