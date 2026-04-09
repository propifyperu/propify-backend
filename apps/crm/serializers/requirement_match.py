from rest_framework import serializers
from apps.crm.models import RequirementMatch


class RequirementMatchSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source="property.title", read_only=True)
    property_code = serializers.CharField(source="property.code", read_only=True)

    class Meta:
        model = RequirementMatch
        fields = [
            "id", "requirement", "property", "property_code", "property_title",
            "score", "details", "computed_at", "is_active",
        ]