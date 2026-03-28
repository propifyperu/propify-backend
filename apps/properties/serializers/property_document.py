from rest_framework import serializers

from apps.properties.models import Property, PropertyDocument


class PropertyDocumentSerializer(serializers.ModelSerializer):
    document_type_name = serializers.CharField(
        source="document_type.name", read_only=True, allow_null=True, default=None
    )

    class Meta:
        model = PropertyDocument
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PropertyWithDocumentsSerializer(serializers.ModelSerializer):
    property_type_name = serializers.CharField(source="property_type.name", read_only=True, allow_null=True, default=None)
    property_subtype_name = serializers.CharField(source="property_subtype.name", read_only=True, allow_null=True, default=None)
    operation_type_name = serializers.CharField(source="operation_type.name", read_only=True, allow_null=True, default=None)
    currency_code = serializers.CharField(source="currency.code", read_only=True, allow_null=True, default=None)
    property_status_name = serializers.CharField(source="property_status.name", read_only=True, allow_null=True, default=None)
    documents = PropertyDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "code",
            "title",
            "price",
            "property_type",
            "property_type_name",
            "property_subtype",
            "property_subtype_name",
            "operation_type",
            "operation_type_name",
            "currency",
            "currency_code",
            "property_status",
            "property_status_name",
            "map_address",
            "display_address",
            "responsible",
            "documents",
        ]
