from django.db import models
from common.models import BaseAuditModel


class District(BaseAuditModel):
    province = models.ForeignKey(
        "locations.Province",
        on_delete=models.PROTECT,
        related_name="districts",
    )
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "district"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["province", "name"], name="uq_district_province_name")
        ]

    def __str__(self) -> str:
        return self.name