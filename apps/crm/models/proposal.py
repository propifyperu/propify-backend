from django.db import models
from common.models import BaseAuditModel
from django.conf import settings


class ProposalStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    CANCELED = "canceled", "Canceled"


class Proposal(BaseAuditModel):
    property = models.ForeignKey("properties.Property", on_delete=models.CASCADE, related_name="proposals")
    lead = models.ForeignKey("crm.Lead", on_delete=models.SET_NULL, null=True, blank=True, related_name="proposals")
    requirement_match = models.ForeignKey("crm.RequirementMatch", on_delete=models.SET_NULL, null=True, blank=True, related_name="proposals")
    currency = models.ForeignKey("catalogs.Currency", on_delete=models.PROTECT, related_name="proposals")
    payment_method = models.ForeignKey("catalogs.PaymentMethod", on_delete=models.PROTECT, related_name="proposals")
    requested_by_user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="proposals_requested",)
    responded_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="proposals_responded",)
    responded_at = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=ProposalStatus.choices, default=ProposalStatus.DRAFT, db_index=True)
    message = models.TextField(blank=True, null=True)
    response_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "proposal"
        ordering = ["-id"]
