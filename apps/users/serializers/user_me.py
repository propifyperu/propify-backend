from rest_framework import serializers

from apps.users.models import User


class UserMeSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(source="role", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True, allow_null=True, default=None)

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
        ]
        read_only_fields = fields
