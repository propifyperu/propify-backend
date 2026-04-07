from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")

    event_type = models.CharField(max_length=80)
    title = models.CharField(max_length=160, blank=True, null=True)
    message = models.TextField()

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    source_object = GenericForeignKey("content_type", "object_id")

    link = models.TextField(blank=True, null=True)
    data = models.JSONField(default=dict, blank=True)

    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event_type", "content_type", "object_id"],
                name="uniq_notification_source",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id} - {self.event_type}"