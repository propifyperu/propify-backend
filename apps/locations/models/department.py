from django.db import models
from common.models import BaseAuditModel


class Department(BaseAuditModel):
    country = models.ForeignKey(
        "locations.Country",
        on_delete=models.PROTECT,
        related_name="departments",
    )
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "department"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["country", "name"], name="uq_department_country_name")
        ]

    def __str__(self) -> str:
        return self.name