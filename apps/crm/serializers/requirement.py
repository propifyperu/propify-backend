from rest_framework import serializers

from apps.crm.models import Requirement, RequirementMatch
from apps.crm.validators import validate_requirement_create, validate_requirement_update
from apps.locations.models import District, Urbanization


class RequirementSerializer(serializers.ModelSerializer):
    operation_type_name = serializers.CharField(
        source="operation_type.name", read_only=True, allow_null=True, default=None
    )
    property_type_name = serializers.CharField(
        source="property_type.name", read_only=True, allow_null=True, default=None
    )
    property_subtype_name = serializers.CharField(
        source="property_subtype.name", read_only=True, allow_null=True, default=None
    )
    property_condition_name = serializers.CharField(
        source="property_condition.name", read_only=True, allow_null=True, default=None
    )
    currency_code = serializers.CharField(
        source="currency.code", read_only=True, allow_null=True, default=None
    )
    payment_method_name = serializers.CharField(
        source="payment_method.name", read_only=True, allow_null=True, default=None
    )
    districts = serializers.PrimaryKeyRelatedField(
        many=True, queryset=District.objects.all(), required=False
    )
    urbanizations = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Urbanization.objects.all(), required=False
    )

    class Meta:
        model = Requirement
        fields = "__all__"
        read_only_fields = [
            "id", "created_at", "updated_at",
            "source_group", "source_date", "notes_message_ws",
            "import_batch", "import_row_sig", "is_active",
        ]

    def validate(self, data):
        if self.instance is None:
            validate_requirement_create(data)
        else:
            validate_requirement_update(self.instance, data)
        return data


class RequirementCreateResponseSerializer(RequirementSerializer):
    matches_count = serializers.SerializerMethodField()

    def get_matches_count(self, obj):
        return obj.requirement_matches.filter(is_active=True).count()

    class Meta(RequirementSerializer.Meta):
        fields = "__all__"