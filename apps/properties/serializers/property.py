import uuid as uuid_lib

from rest_framework import serializers

from apps.properties.models import Property


class PropertySerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)

    property_type_name = serializers.CharField(
        source="property_type.name", read_only=True, allow_null=True, default=None
    )
    property_subtype_name = serializers.CharField(
        source="property_subtype.name", read_only=True, allow_null=True, default=None
    )
    property_condition_name = serializers.CharField(
        source="property_condition.name", read_only=True, allow_null=True, default=None
    )
    operation_type_name = serializers.CharField(
        source="operation_type.name", read_only=True, allow_null=True, default=None
    )
    currency_code = serializers.CharField(
        source="currency.code", read_only=True, allow_null=True, default=None
    )
    payment_method_name = serializers.CharField(
        source="payment_method.name", read_only=True, allow_null=True, default=None
    )
    property_status_name = serializers.CharField(
        source="property_status.name", read_only=True, allow_null=True, default=None
    )

    class Meta:
        model = Property
        fields = "__all__"
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["uuid"] = uuid_lib.uuid4()
        return super().create(validated_data)
