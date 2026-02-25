from django.db import models
from common.models import BaseAuditModel


class Urbanization(BaseAuditModel):
    district = models.ForeignKey(
        "locations.District",
        on_delete=models.PROTECT,
        related_name="urbanizations",
    )
    name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "urbanization"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["district", "name"], name="uq_urbanization_district_name")
        ]

    def __str__(self) -> str:
        return self.name