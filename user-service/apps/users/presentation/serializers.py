"""
apps/users/presentation/serializers.py
DRF Serializers – Presentation layer.

Serializers handle only data shape/validation.
Business logic stays in the domain model.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.users.domain.models import User, Address, Role, UserStatus


# ─── Address ──────────────────────────────────────────────────────────────────

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Address
        fields = ["id", "label", "street", "ward", "district", "city", "country", "is_default"]
        read_only_fields = ["id"]


# ─── Registration ─────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    """
    POST /api/v1/auth/register/
    Customers self-register; role defaults to 'customer'.
    Staff/Admin accounts are created by admins only.
    """
    password         = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model  = User
        fields = ["email", "username", "full_name", "phone", "password", "password_confirm"]

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict) -> User:
        # Always customer on self-registration
        return User.objects.create_user(**validated_data, role=Role.CUSTOMER)


# ─── Public (read-only, no sensitive fields) ──────────────────────────────────

class UserPublicSerializer(serializers.ModelSerializer):
    """Safe read-only view – used in inter-service calls or public listings."""

    class Meta:
        model  = User
        fields = ["id", "username", "full_name", "avatar", "role", "created_at"]
        read_only_fields = fields


# ─── Full Profile (owner or admin) ────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    """
    Full profile serializer.
    Used by: GET /users/me/, admin GET /users/<id>/
    """
    addresses    = AddressSerializer(many=True, read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model  = User
        fields = [
            "id", "email", "username", "full_name", "phone",
            "avatar", "role", "role_display", "status", "is_active",
            "email_verified", "login_count",
            "last_login_ip", "created_at", "updated_at",
            "addresses",
        ]
        read_only_fields = [
            "id", "email", "role", "status", "is_active", "email_verified",
            "login_count", "last_login_ip", "created_at", "updated_at",
        ]


# ─── Admin-level user management ──────────────────────────────────────────────

class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for admin CRUD on users.
    Allows setting role, status, is_staff flags.
    """
    password = serializers.CharField(write_only=True, required=False, min_length=8, style={"input_type": "password"})

    class Meta:
        model  = User
        fields = [
            "id", "email", "username", "full_name", "phone",
            "role", "status", "is_staff", "is_active",
            "email_verified", "login_count", "created_at", "updated_at",
            "password",
        ]
        read_only_fields = ["id", "login_count", "created_at", "updated_at"]

    def validate_role(self, value: str) -> str:
        request = self.context.get("request")
        # Only admins can assign admin role
        if value == Role.ADMIN and request and not request.user.is_admin():
            raise serializers.ValidationError("Only admins can assign the admin role.")
        return value

    def validate(self, attrs: dict) -> dict:
        # If creating a user, password is required
        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Password is required for user creation."})
        return attrs

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password", None)
        role = validated_data.get("role", Role.CUSTOMER)

        # Set default flags based on role
        if role == Role.STAFF:
            validated_data.setdefault("is_staff", True)
            validated_data.setdefault("email_verified", True)
            validated_data.setdefault("status", UserStatus.ACTIVE)
        elif role == Role.ADMIN:
            validated_data.setdefault("is_staff", True)
            validated_data.setdefault("is_superuser", True)
            validated_data.setdefault("email_verified", True)
            validated_data.setdefault("status", UserStatus.ACTIVE)

        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance: User, validated_data: dict) -> User:
        password = validated_data.pop("password", None)
        role = validated_data.get("role")

        if role:
            if role == Role.STAFF:
                validated_data["is_staff"] = True
                validated_data["is_superuser"] = False
            elif role == Role.ADMIN:
                validated_data["is_staff"] = True
                validated_data["is_superuser"] = True
            elif role == Role.CUSTOMER:
                validated_data["is_staff"] = False
                validated_data["is_superuser"] = False

        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


# ─── Profile Update ───────────────────────────────────────────────────────────

class UserUpdateSerializer(serializers.ModelSerializer):
    """PATCH /users/me/ – limited self-editable fields."""

    class Meta:
        model  = User
        fields = ["full_name", "phone", "avatar"]


# ─── Password Change ──────────────────────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    old_password         = serializers.CharField(write_only=True)
    new_password         = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return attrs


# ─── JWT Login (custom payload) ───────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the JWT payload with user claims.
    Other services can decode the token and read role/user_id without DB lookup.
    """

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        # Add custom claims for inter-service use
        token["user_id"]  = str(user.id)
        token["email"]    = user.email
        token["username"] = user.username
        token["role"]     = user.role          # 'admin' | 'staff' | 'customer'
        token["full_name"] = user.full_name
        token["is_staff"] = user.is_staff
        return token

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)

        # Business rule: suspended/inactive accounts cannot log in
        user: User = self.user
        if user.status == UserStatus.SUSPENDED:
            raise serializers.ValidationError("Your account has been suspended. Please contact support.")
        if user.status == UserStatus.INACTIVE:
            raise serializers.ValidationError("Your account is inactive.")

        # Domain action: record the login event
        request = self.context.get("request")
        ip = request.META.get("REMOTE_ADDR") if request else None
        user.record_login(ip)

        # Append user profile to response
        data["user"] = UserSerializer(user).data
        return data
