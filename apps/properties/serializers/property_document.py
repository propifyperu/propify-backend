from rest_framework import serializers

from apps.properties.models import PropertyDocument


class PropertyDocumentSerializer(serializers.ModelSerializer):
    document_type_name = serializers.CharField(
        source="document_type.name", read_only=True, allow_null=True, default=None
    )

    class Meta:
        model = PropertyDocument
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
