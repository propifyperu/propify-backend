from django.conf import settings
from django.db import models
from common.models import BaseAuditModel


class Requirement(BaseAuditModel):
    lead = models.ForeignKey(
        "crm.Lead",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requirements",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_requirements",
    )

    # Catálogos (puedes dejar related_name="requirements" en todos, está OK)
    operation_type = models.ForeignKey(
        "catalogs.OperationType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requirements",
    )
    property_type = models.ForeignKey(
        "catalogs.PropertyType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requirements",
    )
    property_subtype = models.ForeignKey(
        "catalogs.PropertySubtype",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requirements",
    )
    property_condition = models.ForeignKey(
        "catalogs.PropertyCondition",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requirements",
    )

    currency = models.ForeignKey(
        "catalogs.Currency",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requirements",
    )
    payment_method = models.ForeignKey(
        "catalogs.PaymentMethod",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requirements",
    )

    # Ubicación M2M (sin tablas intermedias explícitas)
    districts = models.ManyToManyField(
        "locations.District",
        related_name="requirements",
        blank=True,
    )
    urbanizations = models.ManyToManyField(
        "locations.Urbanization",
        related_name="requirements",
        blank=True,
    )

    # Rangos
    price_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    antiquity_years_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    antiquity_years_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    floors_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    floors_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    bedrooms_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bedrooms_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    bathrooms_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bathrooms_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    garage_spaces_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    garage_spaces_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    land_area_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    land_area_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    built_area_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    built_area_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Booleanos: si quieres 3 estados (True/False/No especificado), pon null=True
    has_elevator = models.BooleanField(null=True, blank=True)
    pet_friendly = models.BooleanField(null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    # Meta / fuente / import (del viejo)
    source_group = models.CharField(max_length=150, null=True, blank=True)
    source_date = models.DateField(null=True, blank=True)
    notes_message_ws = models.TextField(null=True, blank=True)
    import_batch = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    import_row_sig = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "requirement"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(fields=["import_batch", "import_row_sig"], name="uq_requirement_import_row"),
        ]

    def __str__(self) -> str:
        return f"Requirement {self.id}"