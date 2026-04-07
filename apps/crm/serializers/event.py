from rest_framework import serializers

from apps.crm.models import Event
from apps.crm.validators import validate_event_create, validate_event_update


class EventSerializer(serializers.ModelSerializer):
    event_type_name = serializers.CharField(
        source="event_type.name", read_only=True, allow_null=True, default=None
    )

    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ["id", "code", "is_active", "created_at", "updated_at"]

    def validate(self, data):
        if self.instance is None:
            validate_event_create(data)
        else:
            validate_event_update(self.instance, data)
        return data
