"""
apps/users/domain/models.py
Rich Domain Model for User aggregate (DDD).

Hierarchy:
    User (AbstractUser extension, aggregate root)
    └── Address (Value Object, separate table)

Business Rules:
    - Role: 'admin' (full), 'staff' (ops), 'customer' (buy only)
    - Only verified + active customers can place orders
    - Admin cannot be suspended
"""
from __future__ import annotations

import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator


# ─── Role Choices (TextChoices = clean enum) ──────────────────────────────────

class Role(models.TextChoices):
    """
    RBAC Roles aligned with the tiểu luận requirement:
      admin    → full system access
      staff    → manage orders, shipping, products
      customer → browse & purchase only
    """
    ADMIN    = "admin",    "Admin"
    STAFF    = "staff",    "Staff"
    CUSTOMER = "customer", "Customer"


class UserStatus(models.TextChoices):
    ACTIVE    = "active",    "Active"
    INACTIVE  = "inactive",  "Inactive"
    SUSPENDED = "suspended", "Suspended"
    PENDING   = "pending",   "Pending Verification"


# ─── Manager ──────────────────────────────────────────────────────────────────

class UserManager(BaseUserManager):
    """Custom manager – email is the unique identifier."""

    def create_user(self, email: str, password: str, **extra_fields) -> "User":
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        # Default role is customer
        extra_fields.setdefault("role", Role.CUSTOMER)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staff_user(self, email: str, password: str, **extra_fields) -> "User":
        extra_fields.setdefault("role", Role.STAFF)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("status", UserStatus.ACTIVE)
        extra_fields.setdefault("email_verified", True)
        return self.create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)
        extra_fields.setdefault("status", UserStatus.ACTIVE)
        extra_fields.setdefault("email_verified", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# ─── Address (Value Object) ───────────────────────────────────────────────────

class Address(models.Model):
    """Shipping/billing address – value object stored in separate table."""

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey("User", on_delete=models.CASCADE, related_name="addresses")
    label      = models.CharField(max_length=50, default="Home")   # Home / Work / Other
    street     = models.CharField(max_length=255)
    ward       = models.CharField(max_length=100, blank=True)
    district   = models.CharField(max_length=100)
    city       = models.CharField(max_length=100)
    country    = models.CharField(max_length=2, default="VN")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_addresses"
        ordering = ["-is_default", "-created_at"]

    def __str__(self) -> str:
        return f"{self.label}: {self.street}, {self.district}, {self.city}"

    def save(self, *args, **kwargs):
        # Enforce only one default address per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ─── User Aggregate Root ───────────────────────────────────────────────────────

class User(AbstractBaseUser, PermissionsMixin):

    # ── Identity ──────────────────────────────────────────────────────────────
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email     = models.EmailField(unique=True, db_index=True)
    username  = models.CharField(max_length=50, unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    phone     = models.CharField(
        max_length=15, blank=True,
        validators=[RegexValidator(r"^\+?1?\d{9,15}$", "Enter a valid phone number.")]
    )
    avatar    = models.ImageField(upload_to="avatars/", null=True, blank=True)

    # ── Role + Status ─────────────────────────────────────────────────────────
    role   = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
        help_text="admin: full access | staff: ops | customer: buy only",
    )
    status = models.CharField(max_length=20, choices=UserStatus.choices, default=UserStatus.PENDING)

    # ── Verification ──────────────────────────────────────────────────────────
    email_verified    = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    # ── Activity tracking ─────────────────────────────────────────────────────
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_count   = models.PositiveIntegerField(default=0)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    # ── Django auth flags ─────────────────────────────────────────────────────
    is_staff  = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["username", "full_name"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        indexes  = [
            models.Index(fields=["email", "status"]),
            models.Index(fields=["role"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}> [{self.role}]"

    # ── RBAC helpers (used by DRF permission classes) ─────────────────────────

    def is_admin(self) -> bool:
        """True for Admin role OR Django superusers."""
        return self.role == Role.ADMIN or self.is_superuser

    def is_staff_member(self) -> bool:
        """True for Staff or Admin roles."""
        return self.role in (Role.STAFF, Role.ADMIN)

    def is_customer(self) -> bool:
        return self.role == Role.CUSTOMER

    # ── Domain Actions (Rich Domain Model) ────────────────────────────────────

    def verify_email(self) -> None:
        """Invariant: email can only be verified once."""
        if self.email_verified:
            raise ValueError("Email is already verified.")
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.status = UserStatus.ACTIVE
        self.save(update_fields=["email_verified", "email_verified_at", "status", "updated_at"])

    def suspend(self, reason: str = "") -> None:
        """Business rule: Admin accounts cannot be suspended."""
        if self.status == UserStatus.SUSPENDED:
            raise ValueError("User is already suspended.")
        if self.role == Role.ADMIN:
            raise PermissionError("Admin accounts cannot be suspended.")
        self.status = UserStatus.SUSPENDED
        self.save(update_fields=["status", "updated_at"])

    def activate(self) -> None:
        if self.status == UserStatus.ACTIVE and self.is_active:
            raise ValueError("User is already active.")
        self.status = UserStatus.ACTIVE
        self.is_active = True
        self.save(update_fields=["status", "is_active", "updated_at"])

    def record_login(self, ip: str | None) -> None:
        """Domain action: record successful login metadata."""
        self.last_login_ip = ip
        self.login_count  += 1
        self.last_login    = timezone.now()
        self.save(update_fields=["last_login_ip", "login_count", "last_login", "updated_at"])

    def can_place_order(self) -> bool:
        """Business rule: only verified + active customers/staff can place orders."""
        return (
            self.status == UserStatus.ACTIVE
            and self.email_verified
            and self.role in (Role.CUSTOMER, Role.STAFF, Role.ADMIN)
        )

    def get_default_address(self) -> Address | None:
        return self.addresses.filter(is_default=True).first()
