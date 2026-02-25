from django.db import models
from common.models import BaseAuditModel

class UtilityService(BaseAuditModel):
    """
    En tu diagrama: category + name + is_active
    """
    category = models.CharField(max_length=80)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "utility_service"
        ordering = ["category", "name"]
        constraints = [
            models.UniqueConstraint(fields=["category", "name"], name="uq_utility_service_category_name")
        ]

    def __str__(self) -> str:
        return f"{self.category}: {self.name}"