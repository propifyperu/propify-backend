from rest_framework import serializers

from apps.catalogs.models import (
    PropertyType,
    PropertySubtype,
    PropertyStatus,
    PropertyCondition,
    OperationType,
    PaymentMethod,
    Currency,
    DocumentType,
    UtilityService,
    CanalLead,
    LeadStatus,
    EventType,
)


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ["id", "name", "is_active"]


class PropertySubtypeSerializer(serializers.ModelSerializer):
    property_type_name = serializers.CharField(
        source="property_type.name", read_only=True, allow_null=True, default=None
    )

    class Meta:
        model = PropertySubtype
        fields = ["id", "property_type", "property_type_name", "name", "is_active"]


class PropertyStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyStatus
        fields = ["id", "name", "is_active"]


class PropertyConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyCondition
        fields = ["id", "name", "is_active"]


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        fields = ["id", "name", "is_active"]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "name", "is_active"]


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["id", "code", "symbol", "name", "is_active"]


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ["id", "code", "name", "is_active"]


class UtilityServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityService
        fields = ["id", "category", "name", "is_active"]


class CanalLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CanalLead
        fields = ["id", "name", "is_active"]


class LeadStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadStatus
        fields = ["id", "name", "is_active"]


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = ["id", "name", "is_active"]
