from django.db import models
from common.models import BaseAuditModel
from .area import Area

class Role(BaseAuditModel):
    area = models.ForeignKey( Area, on_delete=models.PROTECT, related_name="roles",)
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "role"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name