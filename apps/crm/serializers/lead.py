from rest_framework import serializers

from apps.catalogs.models import OperationType
from apps.crm.models import Lead
from apps.properties.models import Property


class LeadSerializer(serializers.ModelSerializer):
    lead_status_name = serializers.CharField(
        source="lead_status.name", read_only=True, allow_null=True, default=None
    )
    canal_lead_name = serializers.CharField(
        source="canal_lead.name", read_only=True, allow_null=True, default=None
    )
    operation_types = serializers.PrimaryKeyRelatedField(
        many=True, queryset=OperationType.objects.all(), required=False
    )
    properties = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Property.objects.all(), required=False
    )

    class Meta:
        model = Lead
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
