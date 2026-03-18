from rest_framework import serializers

from apps.properties.models import PropertySpecs


class PropertySpecsSerializer(serializers.ModelSerializer):
    water_service_name = serializers.CharField(
        source="water_service.name", read_only=True, allow_null=True, default=None
    )
    energy_service_name = serializers.CharField(
        source="energy_service.name", read_only=True, allow_null=True, default=None
    )
    drainage_service_name = serializers.CharField(
        source="drainage_service.name", read_only=True, allow_null=True, default=None
    )
    gas_service_name = serializers.CharField(
        source="gas_service.name", read_only=True, allow_null=True, default=None
    )

    class Meta:
        model = PropertySpecs
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
