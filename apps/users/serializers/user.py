from rest_framework import serializers
from apps.users.models import User


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
