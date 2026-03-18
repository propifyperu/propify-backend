from rest_framework import serializers

from apps.crm.models import Event


class EventSerializer(serializers.ModelSerializer):
    event_type_name = serializers.CharField(
        source="event_type.name", read_only=True, allow_null=True, default=None
    )

    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
