from rest_framework import serializers
from apps.users.models import User
from apps.users.models.settings import UserSettings


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True, allow_null=True, default=None)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "role",
            "role_name",
            "date_joined",
        ]
        read_only_fields = ["id", "role_name", "date_joined"]


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        exclude = ["user", "created_at", "updated_at", "created_by", "updated_by"]


class UserDetailSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True, allow_null=True, default=None)
    profile = serializers.SerializerMethodField()
    settings = UserSettingsSerializer(read_only=True, allow_null=True, default=None)

    def get_profile(self, obj):
        from apps.users.serializers.user_profile import UserProfileSerializer
        try:
            return UserProfileSerializer(obj.profile, context=self.context).data
        except Exception:
            return None

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "role",
            "role_name",
            "date_joined",
            "profile",
            "settings",
        ]
        read_only_fields = ["id", "role_name", "date_joined", "profile", "settings"]
