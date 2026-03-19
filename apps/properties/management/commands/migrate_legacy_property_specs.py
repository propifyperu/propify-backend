# apps/properties/management/commands/migrate_legacy_property_specs.py
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.utils import timezone


def to_int(val) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def to_decimal(val) -> Optional[Decimal]:
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return None


def to_bool(val) -> Optional[bool]:
    # para campos booleanos típicos (0/1, True/False, "true"/"false")
    if val is None or val == "":
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("1", "true", "t", "yes", "y"):
        return True
    if s in ("0", "false", "f", "no", "n"):
        return False
    return None


def make_aware_if_needed(dt):
    if not dt:
        return dt
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def choice_value_from_label(choices, legacy_label: Optional[str]) -> Optional[str]:
    """
    choices: iterable of (value, label)
    legacy_label: p.ej "Lineal Abierto"
    Retorna value si hace match por label (case-insensitive, trim).
    """
    if not legacy_label:
        return None
    target = " ".join(str(legacy_label).strip().split()).lower()
    for value, label in choices:
        if (" ".join(str(label).strip().split()).lower()) == target:
            return value
    return None


class Command(BaseCommand):
    help = "Migra PropertySpecs desde legacy (Azure SQL) hacia la DB nueva (por Property.code)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")
        parser.add_argument("--limit", type=int, default=None, help="Limita cantidad de registros (debug).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        Property = apps.get_model("properties", "Property")           # modelo nuevo
        PropertySpecs = apps.get_model("properties", "PropertySpecs") # tu modelo nuevo
        UtilityService = apps.get_model("catalogs", "UtilityService") # nuevo catálogo único

        # choices (para mapear por LABEL proveniente de legacy catalog)
        UnitChoices = PropertySpecs._meta.get_field("area_unit").choices
        GarageChoices = PropertySpecs._meta.get_field("garage_type").choices

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración property_specs (legacy → new) =="))

        # ------------------------------------------------------------
        # 1) Leer legacy con LEFT JOIN a catálogos para sacar NOMBRES
        # ------------------------------------------------------------
        sql = """
            SELECT
                p.code,

                p.floors,
                p.unit_location,
                p.bedrooms,
                p.bathrooms,
                p.half_bathrooms,
                p.has_elevator,

                p.land_area,
                lau.name  AS land_area_unit_name,

                p.built_area,
                bau.name  AS built_area_unit_name,

                p.front_measure,
                p.depth_measure,

                p.garage_spaces,
                gt.name   AS garage_type_name,

                p.parking_cost_included,
                p.parking_cost,

                p.antiquity_years,
                p.delivery_date,

                ws.name   AS water_service_name,
                es.name   AS energy_service_name,
                ds.name   AS drainage_service_name,
                gs.name   AS gas_service_name

            FROM properties p
            LEFT JOIN measurement_units lau ON lau.id = p.land_area_unit_id
            LEFT JOIN measurement_units bau ON bau.id = p.built_area_unit_id
            LEFT JOIN garage_types gt       ON gt.id  = p.garage_type_id

            LEFT JOIN water_service_types   ws ON ws.id = p.water_service_id
            LEFT JOIN energy_service_types  es ON es.id = p.energy_service_id
            LEFT JOIN drainage_service_types ds ON ds.id = p.drainage_service_id
            LEFT JOIN gas_service_types     gs ON gs.id = p.gas_service_id

            ORDER BY p.id
        """
        if limit:
            # SQL Server pagination
            sql += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        with connections["legacy"].cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        self.stdout.write(f"Legacy properties leídas: {len(rows)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        created = 0
        updated = 0
        skipped = 0

        def get_or_create_utility(category: str, name: Optional[str]):
            if not name:
                return None
            clean = " ".join(str(name).strip().split())
            if not clean:
                return None
            obj, _ = UtilityService.objects.get_or_create(
                category=category,
                name=clean,
            )
            return obj

        with transaction.atomic():
            for r in rows:
                (
                    legacy_code,

                    legacy_floors,
                    legacy_unit_location,
                    legacy_bedrooms,
                    legacy_bathrooms,
                    legacy_half_bathrooms,
                    legacy_has_elevator,

                    legacy_land_area,
                    legacy_land_area_unit_name,

                    legacy_built_area,
                    legacy_built_area_unit_name,

                    legacy_front_measure,
                    legacy_depth_measure,

                    legacy_garage_spaces,
                    legacy_garage_type_name,

                    legacy_parking_cost_included,
                    legacy_parking_cost,

                    legacy_antiquity_years,
                    legacy_delivery_date,

                    legacy_water_service_name,
                    legacy_energy_service_name,
                    legacy_drainage_service_name,
                    legacy_gas_service_name,
                ) = r

                if not legacy_code:
                    skipped += 1
                    continue

                prop = Property.objects.filter(code=legacy_code).first()
                if not prop:
                    # no existe en new (tal vez no migró), entonces skip
                    self.stdout.write(self.style.WARNING(f"[SKIP] code={legacy_code} no existe en new.Property"))
                    skipped += 1
                    continue

                # choices por LABEL
                area_unit_val = choice_value_from_label(UnitChoices, legacy_land_area_unit_name)
                linear_unit_val = choice_value_from_label(UnitChoices, legacy_built_area_unit_name)
                garage_type_val = choice_value_from_label(GarageChoices, legacy_garage_type_name)

                # utilities (category + name)
                water = get_or_create_utility("water", legacy_water_service_name)
                energy = get_or_create_utility("energy", legacy_energy_service_name)
                drainage = get_or_create_utility("drainage", legacy_drainage_service_name)
                gas = get_or_create_utility("gas", legacy_gas_service_name)

                defaults = {
                    "floors_total": to_int(legacy_floors),
                    # unit_location en legacy es string a veces -> aquí lo forzamos a int si aplica
                    "unit_location": to_int(legacy_unit_location),

                    "bedrooms": to_int(legacy_bedrooms),
                    "bathrooms": to_int(legacy_bathrooms),
                    "half_bathrooms": to_int(legacy_half_bathrooms),

                    # si viene null -> deja default False (tú dijiste: si no hay dato no setees)
                    # PERO como este campo es BooleanField default=False, si ponemos None revienta.
                    # Entonces: solo seteamos si legacy trae True/False.
                }

                be = to_bool(legacy_has_elevator)
                if be is not None:
                    defaults["has_elevator"] = be

                defaults.update(
                    {
                        "land_area": to_decimal(legacy_land_area),
                        "built_area": to_decimal(legacy_built_area),
                        "front_measure": to_decimal(legacy_front_measure),
                        "depth_measure": to_decimal(legacy_depth_measure),

                        "garage_spaces": to_int(legacy_garage_spaces),
                        "parking_cost": to_decimal(legacy_parking_cost),
                    }
                )

                pci = to_bool(legacy_parking_cost_included)
                if pci is not None:
                    defaults["parking_cost_included"] = pci

                if area_unit_val:
                    defaults["area_unit"] = area_unit_val
                # si no matchea, queda None
                if linear_unit_val:
                    defaults["linear_unit"] = linear_unit_val

                if garage_type_val:
                    defaults["garage_type"] = garage_type_val

                defaults["antiquity_years"] = to_int(legacy_antiquity_years)
                defaults["delivery_date"] = legacy_delivery_date  # DateField (pyodbc ya trae date)

                defaults["water_service"] = water
                defaults["energy_service"] = energy
                defaults["drainage_service"] = drainage
                defaults["gas_service"] = gas

                obj, was_created = PropertySpecs.objects.update_or_create(
                    property=prop,
                    defaults=defaults,
                )

                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Migración property_specs OK | created={created} updated={updated} skipped={skipped}"
            )
        )