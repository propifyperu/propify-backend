from django.db import models
from common.models import BaseAuditModel


class Currency(BaseAuditModel):
    code = models.CharField(max_length=3, unique=True)  # PEN, USD
    symbol = models.CharField(max_length=10, blank=True, default="")
    name = models.CharField(max_length=80)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "currency"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code