from django.db import models
from common.models import BaseAuditModel

class UnitChoices(models.TextChoices):
    M2 = "m2", "Metros cuadrados"
    HA = "ha", "Hectareas"
    M  = "m",  "m"
    FT = "ft", "ft"

class GarageTypeChoices(models.TextChoices):
    # deja esto editable, tú lo completas
    LINEAR_OPEN = "LINEAR_OPEN", "Lineal Abierto"
    ROOFED_LINEAR = "ROOFED_LINEAR", "Linear Techado"
    PARALLEL_OPEN = "PARALLEL_OPEN", "Paralelo Abierto"
    PARALLEL_ROOFED = "PARALLEL_ROOFED", "Paralelo Techado"
    OTHER = "OTHER", "Otros"

class PropertySpecs(BaseAuditModel):
    property = models.OneToOneField(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="specs",
    )

    floors_total = models.IntegerField(null=True, blank=True)
    unit_location = models.SmallIntegerField(null=True, blank=True)

    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    half_bathrooms = models.IntegerField(null=True, blank=True)

    has_elevator = models.BooleanField(default=False)

    land_area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    built_area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    front_measure = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    depth_measure = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    area_unit = models.CharField(max_length=10, choices=UnitChoices.choices,null=True, blank=True)
    linear_unit = models.CharField(max_length=10, choices=UnitChoices.choices,null=True, blank=True)

    garage_spaces = models.IntegerField(null=True, blank=True)
    garage_type = models.CharField(max_length=30, choices=GarageTypeChoices.choices,null=True, blank=True)
    parking_cost_included = models.BooleanField(default=False)
    parking_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    antiquity_years = models.SmallIntegerField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)

    has_security = models.BooleanField(default=False)
    has_pool = models.BooleanField(default=False)
    has_garden = models.BooleanField(default=False)
    has_bbq = models.BooleanField(default=False)
    has_terrace = models.BooleanField(default=False)
    has_air_conditioning = models.BooleanField(default=False)
    has_laundry_area = models.BooleanField(default=False)
    has_service_room = models.BooleanField(default=False)
    pet_friendly = models.BooleanField(default=False)

    # servicios (reusa UtilityService como catálogo único por category+name)
    water_service = models.ForeignKey(
        "catalogs.UtilityService",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="water_specs",
    )
    energy_service = models.ForeignKey(
        "catalogs.UtilityService",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="energy_specs",
    )
    drainage_service = models.ForeignKey(
        "catalogs.UtilityService",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drainage_specs",
    )
    gas_service = models.ForeignKey(
        "catalogs.UtilityService",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gas_specs",
    )

    class Meta:
        db_table = "property_specs"

    def __str__(self) -> str:
        return f"Specs - {self.property_id}"