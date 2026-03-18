from rest_framework import serializers

from apps.properties.models import PropertyFinancialInfo


class PropertyFinancialInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyFinancialInfo
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
