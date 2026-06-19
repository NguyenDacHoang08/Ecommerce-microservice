"""
apps/users/admin.py
Django Admin registration for the User domain.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from apps.users.domain.models import User, Address, Role, UserStatus


# ── Address Inline ────────────────────────────────────────────────────────────

class AddressInline(admin.TabularInline):
    model       = Address
    extra       = 0
    fields      = ["label", "street", "ward", "district", "city", "country", "is_default"]
    readonly_fields = ["id"]


# ── User Admin ────────────────────────────────────────────────────────────────

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Custom UserAdmin with role-based display and domain actions.
    """
    model = User

    # ── List view ─────────────────────────────────────────────────────────────
    list_display   = ["email", "username", "full_name", "role_badge", "status_badge",
                      "email_verified", "login_count", "created_at"]
    list_filter    = ["role", "status", "is_staff", "is_active", "email_verified"]
    search_fields  = ["email", "username", "full_name", "phone"]
    ordering       = ["-created_at"]

    # ── Detail view ───────────────────────────────────────────────────────────
    readonly_fields = ["id", "last_login_ip", "login_count", "created_at", "updated_at",
                       "email_verified_at", "last_login"]
    inlines         = [AddressInline]

    fieldsets = (
        ("Identity", {
            "fields": ("id", "email", "username", "full_name", "phone", "avatar"),
        }),
        ("Role & Permissions", {
            "fields": ("role", "is_staff", "is_active", "is_superuser", "groups", "user_permissions"),
        }),
        ("Status & Verification", {
            "fields": ("status", "email_verified", "email_verified_at"),
        }),
        ("Activity", {
            "fields": ("last_login", "last_login_ip", "login_count", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ── Create form configuration ─────────────────────────────────────────────
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields":  ("email", "username", "full_name", "role", "password1", "password2"),
        }),
    )

    # ── Custom display methods ─────────────────────────────────────────────────

    def role_badge(self, obj):
        color_map = {
            Role.ADMIN:    ("#dc2626", "🛡️"),
            Role.STAFF:    ("#2563eb", "👔"),
            Role.CUSTOMER: ("#16a34a", "🛒"),
        }
        color, icon = color_map.get(obj.role, ("#6b7280", "?"))
        return format_html(
            '<span style="color:{};font-weight:bold;">{} {}</span>',
            color, icon, obj.get_role_display()
        )
    role_badge.short_description = "Role"

    def status_badge(self, obj):
        color_map = {
            UserStatus.ACTIVE:    "#16a34a",
            UserStatus.PENDING:   "#d97706",
            UserStatus.SUSPENDED: "#dc2626",
            UserStatus.INACTIVE:  "#6b7280",
        }
        color = color_map.get(obj.status, "#6b7280")
        return format_html(
            '<span style="color:{};font-weight:bold;">● {}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    # ── Bulk Actions ──────────────────────────────────────────────────────────

    actions = ["suspend_users", "activate_users", "verify_emails"]

    @admin.action(description="🚫 Suspend selected users")
    def suspend_users(self, request, queryset):
        count, failed = 0, 0
        for user in queryset:
            try:
                user.suspend()
                count += 1
            except (ValueError, PermissionError):
                failed += 1
        self.message_user(request, f"Suspended: {count}. Skipped (Admin): {failed}.")

    @admin.action(description="✅ Activate selected users")
    def activate_users(self, request, queryset):
        count = 0
        for user in queryset:
            try:
                user.activate()
                count += 1
            except ValueError:
                pass
        self.message_user(request, f"Activated {count} user(s).")

    @admin.action(description="📧 Mark email as verified")
    def verify_emails(self, request, queryset):
        count = 0
        for user in queryset.filter(email_verified=False):
            try:
                user.verify_email()
                count += 1
            except ValueError:
                pass
        self.message_user(request, f"Verified {count} email(s).")


# ── Address Admin ─────────────────────────────────────────────────────────────

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display   = ["user", "label", "street", "district", "city", "country", "is_default"]
    list_filter    = ["country", "is_default"]
    search_fields  = ["user__email", "user__username", "street", "city"]
    readonly_fields = ["id", "created_at"]
