from django.conf import settings
from django.db import models
from common.models import BaseAuditModel


class EventStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "done", "Done"
    REJECTED = "canceled", "Canceled"


class Event(BaseAuditModel):
    code = models.CharField(max_length=50, unique=True)

    event_type = models.ForeignKey("catalogs.EventType", on_delete=models.PROTECT, related_name="events")
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_events",
    )

    lead = models.ForeignKey("crm.Lead", on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    match = models.ForeignKey("crm.Match", on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    property = models.ForeignKey("properties.Property", on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    proposal = models.ForeignKey("crm.Proposal", on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    contact = models.ForeignKey("crm.Contact", on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    tracing = models.TextField(blank=True, null=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.PENDING, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "event"
        ordering = ["-start_time"]
