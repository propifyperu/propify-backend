from rest_framework import serializers

from apps.users.models import User, UserProfile


class _UserProfileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id", "phone", "address", "avatar_url", "birth_date", "nro_document"]
        read_only_fields = fields


class UserMeSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(source="role", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True, allow_null=True, default=None)
    user_profile = _UserProfileNestedSerializer(source="profile", read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role_id",
            "role_name",
            "is_active",
            "is_staff",
            "user_profile",
        ]
        read_only_fields = fields
