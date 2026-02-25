from django.db import models
from common.models import BaseAuditModel


class Province(BaseAuditModel):
    department = models.ForeignKey(
        "locations.Department",
        on_delete=models.PROTECT,
        related_name="provinces",
    )
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "province"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["department", "name"], name="uq_province_department_name")
        ]

    def __str__(self) -> str:
        return self.name