from rest_framework import serializers
from apps.users.models import Area


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "name", "is_active"]
        read_only_fields = fields
