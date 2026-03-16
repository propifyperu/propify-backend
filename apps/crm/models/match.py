from django.conf import settings
from django.db import models
from common.models import BaseAuditModel


class MatchStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CANCELED = "canceled", "Canceled"


class Match(BaseAuditModel):
    property = models.ForeignKey("properties.Property", on_delete=models.CASCADE, related_name="matches")

    requested_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_matches",
    )
    lead = models.ForeignKey("crm.Lead", on_delete=models.SET_NULL, null=True, blank=True, related_name="matches")
    requirement = models.ForeignKey("crm.Requirement", on_delete=models.SET_NULL, null=True, blank=True, related_name="matches")
    requirementmatch = models.ForeignKey(
        "crm.RequirementMatch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches",
    )

    match_status = models.CharField(max_length=20, choices=MatchStatus.choices, default=MatchStatus.PENDING, db_index=True)
    message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "match"
        ordering = ["-id"]