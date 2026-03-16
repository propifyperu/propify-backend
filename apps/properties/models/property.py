from django.conf import settings
from django.db import models
from common.models import BaseAuditModel


class Property(BaseAuditModel):
    """
    Modelo principal del inmueble (publicación).
    """

    # Relaciones core
    contact = models.ForeignKey(
        "crm.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="properties",
    )
    property_type = models.ForeignKey(
        "catalogs.PropertyType",
        on_delete=models.PROTECT,
        related_name="properties",
    )
    property_subtype = models.ForeignKey(
        "catalogs.PropertySubtype",
        on_delete=models.PROTECT,
        related_name="properties",
    )
    property_condition = models.ForeignKey(
        "catalogs.PropertyCondition",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="properties",
    )
    operation_type = models.ForeignKey(
        "catalogs.OperationType",
        on_delete=models.PROTECT,
        related_name="properties",
    )
    currency = models.ForeignKey(
        "catalogs.Currency",
        on_delete=models.PROTECT,
        related_name="properties",
    )
    payment_method = models.ForeignKey(
        "catalogs.PaymentMethod",
        on_delete=models.PROTECT,
        related_name="properties",
    )

    district = models.ForeignKey(
        "locations.District",
        on_delete=models.PROTECT,
        related_name="properties",
    )
    urbanization = models.ForeignKey(
        "locations.Urbanization",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="properties",
    )

    property_status = models.ForeignKey(
        "catalogs.PropertyStatus",
        on_delete=models.PROTECT,
        related_name="properties",
    )

    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responsible_properties",
    )

    # WordPress sync
    wp_post_id = models.IntegerField(null=True, blank=True, db_index=True)
    wp_slug = models.SlugField(null=True, blank=True)
    wp_last_sync = models.DateTimeField(null=True, blank=True)

    # Campos de publicación
    is_project = models.BooleanField(default=False)
    project_name = models.CharField(max_length=200, null=True, blank=True)

    uuid = models.UUIDField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    maintenance_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    map_address = models.CharField(max_length=255, blank=True, null=True) #address api google
    display_address = models.CharField(max_length=255, blank=True, null=True) #address custom

    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    registry_number = models.CharField(max_length=80, blank=True, null=True)

    class Meta:
        db_table = "property"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.id} - {self.title}"