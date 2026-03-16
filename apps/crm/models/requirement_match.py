from django.db import models
from common.models import BaseAuditModel


class RequirementMatch(BaseAuditModel):
    requirement = models.ForeignKey("crm.Requirement", on_delete=models.CASCADE, related_name="matches")
    property = models.ForeignKey("properties.Property", on_delete=models.CASCADE, related_name="requirement_matches")

    score = models.DecimalField(max_digits=6, decimal_places=2)  # 0..100
    details = models.JSONField(default=dict, blank=True)
    computed_at = models.DateTimeField(db_index=True)

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "requirement_match"
        indexes = [
            models.Index(fields=["requirement", "-score"]),
            models.Index(fields=["property", "-score"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["requirement", "property", "computed_at"], name="uq_requirement_match_run"),
        ]