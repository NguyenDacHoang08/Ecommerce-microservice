"""
apps/core/permissions.py
Custom DRF Permission classes implementing RBAC.

Permission matrix:
    ┌──────────────────────────┬─────────┬───────┬──────────┐
    │ Action                   │ Admin   │ Staff │ Customer │
    ├──────────────────────────┼─────────┼───────┼──────────┤
    │ List/Read all users      │   ✓     │   ✓   │    ✗     │
    │ Create/Edit/Delete users │   ✓     │   ✗   │    ✗     │
    │ Assign roles             │   ✓     │   ✗   │    ✗     │
    │ Manage own profile       │   ✓     │   ✓   │    ✓     │
    │ Manage orders/shipping   │   ✓     │   ✓   │    ✗     │
    │ Suspend/Activate user    │   ✓     │   ✗   │    ✗     │
    └──────────────────────────┴─────────┴───────┴──────────┘
"""
from django.conf import settings
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS


class IsAdmin(BasePermission):
    """Full access: only Role.ADMIN or superuser."""
    message = "Admin access required."

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_admin()
        )


class IsStaffOrAdmin(BasePermission):
    """Staff + Admin: operations access (orders, shipping, products)."""
    message = "Staff or Admin access required."

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff_member()
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level: owner can read/modify their own data.
    Admin can access any object.
    """
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Admin always allowed
        if user.is_admin():
            return True
        # Safe methods allowed for staff
        if request.method in SAFE_METHODS and user.is_staff_member():
            return True
        # Owner check: obj may be User or related (Address)
        owner = getattr(obj, "user", obj)
        return owner == user


class IsAdminOrReadOnly(BasePermission):
    """Read-only for all authenticated; write only for admin."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_admin()


class IsCustomer(BasePermission):
    """Mainly for order placement – customers, staff, and admin."""
    message = "Customer account required to perform this action."

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.can_place_order()
        )


class InternalServicePermission(BasePermission):
    """
    Service-to-service permission.
    Other microservices pass a shared secret header: X-Internal-Token.
    """
    message = "Internal service token required."

    def has_permission(self, request, view) -> bool:
        token = request.headers.get("X-Internal-Token")
        service_secret = getattr(settings, "INTERNAL_SERVICE_SECRET", None)
        if not service_secret:
            return False
        return token == service_secret
