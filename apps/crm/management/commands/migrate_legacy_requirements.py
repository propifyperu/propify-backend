# apps/crm/management/commands/migrate_legacy_requirements.py
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connections, transaction


User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_decimal(val) -> Optional[Decimal]:
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return None


def to_bool(val) -> Optional[bool]:
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


def clean_str(val) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Migra Requirements desde legacy (Azure SQL) hacia la DB nueva."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")
        parser.add_argument("--limit", type=int, default=None, help="Limita cantidad de filas (debug).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        Requirement        = apps.get_model("crm", "Requirement")
        OperationType      = apps.get_model("catalogs", "OperationType")
        PropertyType       = apps.get_model("catalogs", "PropertyType")
        PropertySubtype    = apps.get_model("catalogs", "PropertySubtype")
        PropertyCondition  = apps.get_model("catalogs", "PropertyCondition")
        Currency           = apps.get_model("catalogs", "Currency")
        PaymentMethod      = apps.get_model("catalogs", "PaymentMethod")
        District           = apps.get_model("locations", "District")

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración requirements (legacy → new) =="))

        # ------------------------------------------------------------------
        # 1) Leer legacy requirements con todos los JOIN necesarios
        # ------------------------------------------------------------------
        sql = """
            SELECT
                r.id                    AS legacy_id,

                -- auditoría
                u_created.username      AS created_by_username,
                u_assigned.username     AS assigned_to_username,
                r.created_at,
                r.updated_at,
                r.is_active,

                -- catálogos (traemos NOMBRES para buscar en new)
                ot.name                 AS operation_type_name,
                pt.name                 AS property_type_name,
                ps_sub.name             AS property_subtype_name,
                ps_cond.name            AS property_status_name,
                cur.name                AS currency_name,
                pm.name                 AS payment_method_name,

                -- rangos
                r.price_min,
                r.price_max,
                r.antiquity_years_min,
                r.antiquity_years_max,
                r.floors_min,
                r.floors_max,
                r.bedrooms_min,
                r.bedrooms_max,
                r.bathrooms_min,
                r.bathrooms_max,
                r.garage_spaces_min,
                r.garage_spaces_max,
                r.land_area_min,
                r.land_area_max,
                r.built_area_min,
                r.built_area_max,

                -- booleanos y texto
                r.has_elevator,
                r.pet_friendly,
                r.notes,
                r.source_group,
                r.source_date,
                r.notes_message_ws,
                r.import_batch,
                r.import_row_sig

            FROM requirements r
            LEFT JOIN users u_created  ON u_created.id  = r.created_by_id
            LEFT JOIN users u_assigned ON u_assigned.id = r.assigned_to_id
            LEFT JOIN operation_types  ot      ON ot.id      = r.operation_type_id
            LEFT JOIN property_types   pt      ON pt.id      = r.property_type_id
            LEFT JOIN property_subtypes ps_sub ON ps_sub.id  = r.property_subtype_id
            LEFT JOIN property_statuses ps_cond ON ps_cond.id = r.property_status_id
            LEFT JOIN currencies       cur     ON cur.id     = r.currency_id
            LEFT JOIN payment_methods  pm      ON pm.id      = r.payment_method_id
            ORDER BY r.id
        """
        if limit:
            sql += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        # Leer tabla intermedia de districts M2M
        # JOIN directo con properties_district (tabla de new accesible desde legacy
        # via mismo servidor, o bien leemos el district_id y buscamos en new por ID legacy)
        # Como legacy no tiene tabla 'districts' separada, traemos requirement_id + district_id
        # y luego buscamos en new.District por el legacy_id si existe, o lo saltamos.
        sql_districts = """
            SELECT requirement_id, district_id
            FROM requirements_districts
            ORDER BY requirement_id
        """

        with connections["legacy"].cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            self.stdout.write(f"Legacy requirements: {len(rows)}")

            cursor.execute(sql_districts)
            legacy_req_districts = cursor.fetchall()
            self.stdout.write(f"Legacy requirement_districts: {len(legacy_req_districts)}")

        # req_districts_map: legacy_req_id -> list of legacy district_id (int)
        req_districts_map: dict[int, list[int]] = {}
        for req_id, dist_id in legacy_req_districts:
            if dist_id is not None:
                req_districts_map.setdefault(int(req_id), []).append(int(dist_id))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        # ------------------------------------------------------------------
        # 2) Pre-cargar catálogos new en memoria para evitar N+1
        # ------------------------------------------------------------------
        op_type_cache      = {o.name.strip().lower(): o for o in OperationType.objects.all()}
        prop_type_cache    = {o.name.strip().lower(): o for o in PropertyType.objects.all()}
        prop_subtype_cache = {o.name.strip().lower(): o for o in PropertySubtype.objects.all()}
        prop_cond_cache    = {o.name.strip().lower(): o for o in PropertyCondition.objects.all()}
        currency_cache     = {o.name.strip().lower(): o for o in Currency.objects.all()}
        payment_cache      = {o.name.strip().lower(): o for o in PaymentMethod.objects.all()}
        district_cache     = {o.id: o for o in District.objects.all()}
        user_cache         = {u.username.strip().lower(): u for u in User.objects.all()}

        def lookup(cache: dict, name: Optional[str], label: str, legacy_id: int):
            if not name:
                return None
            key = name.strip().lower()
            obj = cache.get(key)
            if not obj:
                self.stdout.write(
                    self.style.WARNING(
                        f"[WARN] req legacy_id={legacy_id} {label}='{name}' no encontrado en new -> NULL"
                    )
                )
            return obj

        # ------------------------------------------------------------------
        # 3) Migrar
        # ------------------------------------------------------------------
        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for row in rows:
                (
                    legacy_id,
                    created_by_username,
                    assigned_to_username,
                    created_at,
                    updated_at,
                    is_active,
                    operation_type_name,
                    property_type_name,
                    property_subtype_name,
                    property_status_name,
                    currency_name,
                    payment_method_name,
                    price_min,
                    price_max,
                    antiquity_years_min,
                    antiquity_years_max,
                    floors_min,
                    floors_max,
                    bedrooms_min,
                    bedrooms_max,
                    bathrooms_min,
                    bathrooms_max,
                    garage_spaces_min,
                    garage_spaces_max,
                    land_area_min,
                    land_area_max,
                    built_area_min,
                    built_area_max,
                    has_elevator,
                    pet_friendly,
                    notes,
                    source_group,
                    source_date,
                    notes_message_ws,
                    import_batch,
                    import_row_sig,
                ) = row

                legacy_id = int(legacy_id)

                # Auditoría
                created_by_obj  = lookup(user_cache, created_by_username,  "created_by",  legacy_id)
                assigned_to_obj = lookup(user_cache, assigned_to_username, "assigned_to", legacy_id)

                # Catálogos
                op_type_obj      = lookup(op_type_cache,      operation_type_name,    "operation_type",     legacy_id)
                prop_type_obj    = lookup(prop_type_cache,    property_type_name,     "property_type",      legacy_id)
                prop_subtype_obj = lookup(prop_subtype_cache, property_subtype_name,  "property_subtype",   legacy_id)
                prop_cond_obj    = lookup(prop_cond_cache,    property_status_name,   "property_condition", legacy_id)
                currency_obj     = lookup(currency_cache,     currency_name,          "currency",           legacy_id)
                payment_obj      = lookup(payment_cache,      payment_method_name,    "payment_method",     legacy_id)

                # import_batch + import_row_sig como clave de upsert (igual que en legacy)
                ib  = clean_str(import_batch)
                irs = clean_str(import_row_sig)

                defaults = {
                    # auditoría
                    "created_by":  created_by_obj,
                    "updated_by":  None,           # no existe updated_by en legacy
                    "assigned_to": assigned_to_obj,
                    "created_at":  created_at,
                    "updated_at":  updated_at,
                    "is_active":   bool(is_active) if is_active is not None else True,

                    # lead y urbanizations -> NULL (según mapping)
                    "lead":          None,

                    # catálogos
                    "operation_type":     op_type_obj,
                    "property_type":      prop_type_obj,
                    "property_subtype":   prop_subtype_obj,
                    "property_condition": prop_cond_obj,
                    "currency":           currency_obj,
                    "payment_method":     payment_obj,

                    # rangos
                    "price_min":            to_decimal(price_min),
                    "price_max":            to_decimal(price_max),
                    "antiquity_years_min":  to_decimal(antiquity_years_min),
                    "antiquity_years_max":  to_decimal(antiquity_years_max),
                    "floors_min":           to_decimal(floors_min),
                    "floors_max":           to_decimal(floors_max),
                    "bedrooms_min":         to_decimal(bedrooms_min),
                    "bedrooms_max":         to_decimal(bedrooms_max),
                    "bathrooms_min":        to_decimal(bathrooms_min),
                    "bathrooms_max":        to_decimal(bathrooms_max),
                    "garage_spaces_min":    to_decimal(garage_spaces_min),
                    "garage_spaces_max":    to_decimal(garage_spaces_max),
                    "land_area_min":        to_decimal(land_area_min),
                    "land_area_max":        to_decimal(land_area_max),
                    "built_area_min":       to_decimal(built_area_min),
                    "built_area_max":       to_decimal(built_area_max),

                    # booleanos
                    "has_elevator": to_bool(has_elevator),
                    "pet_friendly": to_bool(pet_friendly),

                    # texto
                    "notes":            clean_str(notes),
                    "source_group":     clean_str(source_group),
                    "source_date":      source_date,
                    "notes_message_ws": clean_str(notes_message_ws),
                    "import_batch":     ib,
                    "import_row_sig":   irs,
                }

                # Estrategia de upsert:
                # Si tiene import_batch + import_row_sig -> usar UniqueConstraint
                # Si no -> crear siempre (no hay forma segura de deduplicar)
                if ib and irs:
                    obj, was_created = Requirement.objects.update_or_create(
                        import_batch=ib,
                        import_row_sig=irs,
                        defaults=defaults,
                    )
                else:
                    # Sin clave de deduplicación: crear nuevo
                    obj = Requirement(**defaults)
                    obj.save()
                    was_created = True

                # M2M districts — buscamos por id (legacy district_id == new District.id)
                district_ids = req_districts_map.get(legacy_id, [])
                if district_ids:
                    district_objs = []
                    for did in district_ids:
                        d = district_cache.get(did)
                        if d:
                            district_objs.append(d)
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"[WARN] req legacy_id={legacy_id} district_id={did} no encontrado en new -> skip"
                                )
                            )
                    if district_objs:
                        obj.districts.set(district_objs)

                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Migración requirements OK | created={created} updated={updated} skipped={skipped}"
            )
        )
