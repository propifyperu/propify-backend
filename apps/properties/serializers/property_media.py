from rest_framework import serializers

from apps.properties.models import PropertyMedia


class PropertyMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyMedia
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
