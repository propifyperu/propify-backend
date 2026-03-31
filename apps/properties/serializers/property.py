import uuid as uuid_lib

from rest_framework import serializers

from apps.properties.models import Property, PropertyMedia, PropertySpecs
from apps.properties.serializers.property_specs import PropertySpecsSerializer
from apps.properties.serializers.property_media import PropertyMediaSerializer
from apps.properties.serializers.property_financial_info import PropertyFinancialInfoSerializer
from apps.properties.serializers.property_document import PropertyDocumentSerializer


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


# ---------------------------------------------------------------------------
# Cards serializers (listado compacto para tarjetas del frontend)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Full detail serializer (lectura completa con todos los sub-objetos)
# ---------------------------------------------------------------------------

class PropertyFullDetailSerializer(serializers.ModelSerializer):
    property_type_name = serializers.CharField(source="property_type.name", read_only=True, allow_null=True, default=None)
    property_subtype_name = serializers.CharField(source="property_subtype.name", read_only=True, allow_null=True, default=None)
    property_condition_name = serializers.CharField(source="property_condition.name", read_only=True, allow_null=True, default=None)
    operation_type_name = serializers.CharField(source="operation_type.name", read_only=True, allow_null=True, default=None)
    currency_code = serializers.CharField(source="currency.code", read_only=True, allow_null=True, default=None)
    payment_method_name = serializers.CharField(source="payment_method.name", read_only=True, allow_null=True, default=None)
    property_status_name = serializers.CharField(source="property_status.name", read_only=True, allow_null=True, default=None)

    specs = PropertySpecsSerializer(read_only=True)
    financial = PropertyFinancialInfoSerializer(read_only=True)
    media = PropertyMediaSerializer(many=True, read_only=True)
    documents = PropertyDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = "__all__"



class PropertyLandingDetailSerializer(serializers.ModelSerializer):
    property_type_name = serializers.CharField(source="property_type.name", read_only=True, allow_null=True, default=None)
    property_subtype_name = serializers.CharField(source="property_subtype.name", read_only=True, allow_null=True, default=None)
    property_condition_name = serializers.CharField(source="property_condition.name", read_only=True, allow_null=True, default=None)
    operation_type_name = serializers.CharField(source="operation_type.name", read_only=True, allow_null=True, default=None)
    currency_code = serializers.CharField(source="currency.code", read_only=True, allow_null=True, default=None)
    payment_method_name = serializers.CharField(source="payment_method.name", read_only=True, allow_null=True, default=None)
    property_status_name = serializers.CharField(source="property_status.name", read_only=True, allow_null=True, default=None)
    district_name = serializers.CharField(source="district.name", read_only=True, allow_null=True, default=None)

    specs = PropertySpecsSerializer(read_only=True)
    media = PropertyMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = "__all__"


class PropertyCardSpecsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertySpecs
        fields = ["land_area", "built_area", "front_measure", "depth_measure", "bedrooms", "bathrooms"]


class PropertyCardMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyMedia
        fields = ["media_type", "file", "order"]


class PropertyCardSerializer(serializers.ModelSerializer):
    property_type_name = serializers.CharField(source="property_type.name", read_only=True, allow_null=True, default=None)
    property_subtype_name = serializers.CharField(source="property_subtype.name", read_only=True, allow_null=True, default=None)
    property_condition_name = serializers.CharField(source="property_condition.name", read_only=True, allow_null=True, default=None)
    operation_type_name = serializers.CharField(source="operation_type.name", read_only=True, allow_null=True, default=None)
    currency_code = serializers.CharField(source="currency.code", read_only=True, allow_null=True, default=None)
    property_status_name = serializers.CharField(source="property_status.name", read_only=True, allow_null=True, default=None)
    specs = PropertyCardSpecsSerializer(read_only=True)
    media = PropertyCardMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "code",
            "property_type",
            "property_type_name",
            "property_subtype",
            "property_subtype_name",
            "property_condition",
            "property_condition_name",
            "operation_type",
            "operation_type_name",
            "currency",
            "currency_code",
            "price",
            "title",
            "map_address",
            "display_address",
            "property_status",
            "property_status_name",
            "responsible",
            "specs",
            "media",
        ]


class PropertyWithSpecsSerializer(serializers.ModelSerializer):
    property_type_name = serializers.CharField(source="property_type.name", read_only=True)
    property_subtype_name = serializers.CharField(source="property_subtype.name", read_only=True)
    property_condition_name = serializers.CharField(source="property_condition.name", read_only=True)
    operation_type_name = serializers.CharField(source="operation_type.name", read_only=True)
    currency_code = serializers.CharField(source="currency.code", read_only=True)
    property_status_name = serializers.CharField(source="property_status.name", read_only=True)

    specs = PropertySpecsSerializer(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "code",
            "property_type",
            "property_type_name",
            "property_subtype",
            "property_subtype_name",
            "property_condition",
            "property_condition_name",
            "operation_type",
            "operation_type_name",
            "currency",
            "currency_code",
            "price",
            "title",
            "map_address",
            "display_address",
            "property_status",
            "property_status_name",
            "responsible",
            "specs",
        ]