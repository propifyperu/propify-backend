from django.db import models
from common.models import BaseAuditModel


class PropertyDocument(BaseAuditModel):
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.ForeignKey(
        "catalogs.DocumentType",
        on_delete=models.PROTECT,
        related_name="property_documents",
    )

    file = models.FileField(upload_to="properties/documents/", null=True, blank=True)

    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "property_document"
        indexes = [
            models.Index(fields=["property", "document_type"]),
        ]

    def __str__(self) -> str:
        return f"Doc - {self.property_id} - {self.document_type_id}"