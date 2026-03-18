from rest_framework import serializers
from apps.users.models import Role


class RoleSerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source="area.name", read_only=True)

    class Meta:
        model = Role
        fields = ["id", "area", "area_name", "name", "is_active"]
        read_only_fields = ["id", "area_name"]
