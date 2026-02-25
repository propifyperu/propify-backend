from django.db import models
from common.models import BaseAuditModel

class DocumentType(BaseAuditModel):
    code = models.CharField(max_length=60, unique=True)  # dni, partida_registral, etc.
    name = models.CharField(max_length=140)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "document_type"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name