from django.db import models
from common.models import BaseAuditModel
from .property_type import PropertyType

class PropertySubtype(BaseAuditModel):
    property_type = models.ForeignKey(PropertyType, on_delete=models.PROTECT, related_name="subtypes",)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "property_subtype"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["property_type", "name"], name="uq_property_subtype_type_name")
        ]

    def __str__(self) -> str:
        return f"{self.property_type.name} - {self.name}"