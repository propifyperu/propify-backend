from rest_framework import serializers
from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "event_type",
            "title",
            "message",
            "content_type",
            "object_id",
            "data",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "user", "event_type", "title", "message", "content_type", "object_id", "data", "created_at"]
