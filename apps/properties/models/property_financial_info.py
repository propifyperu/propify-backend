from django.db import models
from common.models import BaseAuditModel

class ContractTypeChoices(models.TextChoices):
    EXCLUSIVE = "exclusive", "Exclusive"
    SEMI_EXCLUSIVE = "semi_exclusive", "Semi exclusive"
    NON_EXCLUSIVE = "non_exclusive", "Non exclusive"

class PropertyFinancialInfo(BaseAuditModel):
    property = models.OneToOneField(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="financial",
    )

    commission_initial = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    commission_final = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    commission_pf = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True) #comision propify
    contract_type = models.CharField(max_length=30, choices=ContractTypeChoices.choices, blank=True, null=True)
    negotiation_status = models.CharField(max_length=50, blank=True, null=True)  # MVP

    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "property_financial_info"

    def __str__(self) -> str:
        return f"Financial - {self.property_id}"