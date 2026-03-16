from django.db import models
from common.models import BaseAuditModel


class PropertyMediaType(models.TextChoices):
    IMAGE = "image", "Image" #image, valor guardado en BD, Image label humano
    VIDEO = "video", "Video"


class PropertyMedia(BaseAuditModel):
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="media",
    )

    media_type = models.CharField(max_length=20, choices=PropertyMediaType.choices)
    file = models.FileField(upload_to="properties/media/", null=True, blank=True)

    title = models.CharField(max_length=255, blank=True, null=True)
    label = models.CharField(max_length=255, blank=True, null=True)
    order = models.IntegerField(default=0)

    wp_media_id = models.IntegerField(null=True, blank=True, db_index=True)
    wp_source_url = models.URLField(max_length=1000, null=True, blank=True)
    wp_last_sync = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "property_media"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.media_type} - {self.property_id}"