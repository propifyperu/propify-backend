# apps/properties/management/commands/migrate_legacy_properties.py
from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.utils import timezone


def make_aware_if_needed(dt):
    if not dt:
        return dt
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def to_decimal(val):
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return None


def parse_coords(value: str | None):
    if not value:
        return (None, None)
    try:
        parts = [p.strip() for p in str(value).split(",")]
        if len(parts) != 2:
            return (None, None)
        return (Decimal(parts[0]), Decimal(parts[1]))
    except (InvalidOperation, ValueError):
        return (None, None)


def norm(s: str | None) -> str | None:
    if not s:
        return None
    return " ".join(str(s).strip().split())


def legacy_table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME = %s
        """,
        [table_name],
    )
    return cursor.fetchone() is not None


def find_legacy_table(cursor, candidates: list[str]) -> str | None:
    for t in candidates:
        try:
            if legacy_table_exists(cursor, t):
                return t
        except Exception:
            continue
    return None


def build_legacy_lookup(cursor, table_candidates: list[str], id_col="id", name_col="name") -> dict[int, str]:
    table = find_legacy_table(cursor, table_candidates)
    if not table:
        return {}
    sql = f"SELECT {id_col}, {name_col} FROM {table}"
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        out: dict[int, str] = {}
        for rid, rname in rows:
            try:
                out[int(rid)] = str(rname) if rname is not None else ""
            except Exception:
                continue
        return out
    except Exception:
        return {}


def pick_by_name(qs, name: str | None):
    n = norm(name)
    if not n:
        return None
    return qs.filter(name__iexact=n).first()


def resolve_responsible_user(User, legacy_responsible_id: int | None, legacy_resp_name: str | None):
    """
    Buscar responsible por username (y fallbacks).
    """
    if legacy_responsible_id:
        u = User.objects.filter(id=legacy_responsible_id).first()
        if u:
            return u

    n = norm(legacy_resp_name)
    if not n:
        return None

    u = User.objects.filter(username__iexact=n).first()
    if u:
        return u

    u = User.objects.filter(email__iexact=n).first()
    if u:
        return u

    parts = n.split(" ")
    if len(parts) >= 2:
        first = parts[0]
        last = " ".join(parts[1:])
        u = User.objects.filter(first_name__iexact=first, last_name__iexact=last).first()
        if u:
            return u

    return None


class Command(BaseCommand):
    help = "Migra properties desde legacy (Azure SQL) hacia la DB nueva."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")
        parser.add_argument("--limit", type=int, default=None, help="Limita cantidad de registros (debug).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        Property = apps.get_model("properties", "Property")

        PropertyType = apps.get_model("catalogs", "PropertyType")
        PropertySubtype = apps.get_model("catalogs", "PropertySubtype")
        PropertyCondition = apps.get_model("catalogs", "PropertyCondition")
        OperationType = apps.get_model("catalogs", "OperationType")
        Currency = apps.get_model("catalogs", "Currency")
        PaymentMethod = apps.get_model("catalogs", "PaymentMethod")
        PropertyStatus = apps.get_model("catalogs", "PropertyStatus")

        District = apps.get_model("locations", "District")
        Urbanization = apps.get_model("locations", "Urbanization")

        User = apps.get_model("users", "User")

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración properties (legacy → new) =="))

        # ------------------------------------------------------------------
        # Defaults que SÍ quieres
        # ------------------------------------------------------------------
        # operation_type default = Venta (si no existe, crearlo)
        default_op, _ = OperationType.objects.get_or_create(name="Venta")

        sql = """
            SELECT
                id,
                code,
                codigo_unico_propiedad,
                title,
                description,

                property_type_id,
                property_subtype_id,
                status_id,
                condition_id,
                operation_type_id,
                currency_id,
                forma_de_pago_id,

                availability_status,

                district_fk_id,
                urbanization_fk_id,

                responsible_id,

                price,
                maintenance_fee,

                exact_address,
                real_address,
                coordinates,

                wp_post_id,
                wp_slug,
                wp_last_sync,

                created_at,
                updated_at,
                is_active
            FROM properties
            ORDER BY id
        """
        if limit:
            sql += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        with connections["legacy"].cursor() as cursor:
            legacy_property_types = build_legacy_lookup(cursor, ["property_types", "property_type", "dbo.property_types"])
            legacy_property_subtypes = build_legacy_lookup(cursor, ["property_subtypes", "property_subtype", "dbo.property_subtypes"])
            legacy_property_statuses = build_legacy_lookup(cursor, ["property_statuses", "property_status", "dbo.property_statuses"])
            legacy_operation_types = build_legacy_lookup(cursor, ["operation_types", "operation_type", "dbo.operation_types"])
            legacy_currencies = build_legacy_lookup(cursor, ["currencies", "currency", "dbo.currencies"])
            legacy_payment_methods = build_legacy_lookup(cursor, ["payment_methods", "payment_method", "dbo.payment_methods"])
            legacy_districts = build_legacy_lookup(cursor, ["districts", "district", "dbo.districts", "dbo.district"])
            legacy_urbanizations = build_legacy_lookup(cursor, ["urbanizations", "urbanization", "dbo.urbanizations", "dbo.urbanization"])

            # users legacy -> username/email/name best-effort
            legacy_users_table = find_legacy_table(
                cursor,
                ["users_user", "auth_user", "users", "dbo.users_user", "dbo.auth_user"],
            )
            legacy_user_name_by_id: dict[int, str] = {}
            if legacy_users_table:
                candidate_sqls = [
                    f"SELECT id, username FROM {legacy_users_table}",
                    f"SELECT id, email FROM {legacy_users_table}",
                    f"SELECT id, CONCAT(first_name,' ',last_name) as name FROM {legacy_users_table}",
                ]
                for ns in candidate_sqls:
                    try:
                        cursor.execute(ns)
                        urows = cursor.fetchall()
                        tmp = {}
                        for uid, uname in urows:
                            try:
                                tmp[int(uid)] = str(uname).strip() if uname is not None else ""
                            except Exception:
                                continue
                        if any(v for v in tmp.values()):
                            legacy_user_name_by_id = tmp
                            break
                    except Exception:
                        continue

            cursor.execute(sql)
            rows = cursor.fetchall()

        self.stdout.write(f"Properties legacy: {len(rows)}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        # availability_status legacy -> nombre para PropertyStatus (new)
        # Tu regla: si no existe, CREARLO.
        availability_to_name = {
            "available": "Disponible",
            "reserved": "Reservada",
            "sold": "Vendida",          # si no existe en tu catálogo, se crea
            "unavailable": "No disponible",
            "paused": "Pausada",
            "catchment": "En proceso de captacion",  # si no existe, se crea
        }

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for r in rows:
                (
                    legacy_id,
                    legacy_code,
                    legacy_cup,
                    legacy_title,
                    legacy_description,

                    legacy_property_type_id,
                    legacy_property_subtype_id,
                    legacy_status_id,
                    legacy_condition_id,  # no usado
                    legacy_operation_type_id,
                    legacy_currency_id,
                    legacy_payment_method_id,

                    legacy_availability_status,

                    legacy_district_id,
                    legacy_urbanization_id,

                    legacy_responsible_id,

                    legacy_price,
                    legacy_maintenance_fee,  # no se migra

                    legacy_exact_address,
                    legacy_real_address,
                    legacy_coordinates,

                    legacy_wp_post_id,
                    legacy_wp_slug,
                    legacy_wp_last_sync,

                    legacy_created_at,
                    legacy_updated_at,
                    legacy_is_active,
                ) = r

                # property_type por NAME
                pt_name = legacy_property_types.get(int(legacy_property_type_id or 0))
                pt = pick_by_name(PropertyType.objects.all(), pt_name) or PropertyType.objects.filter(id=legacy_property_type_id).first()
                if not pt:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"[SKIP] legacy_id={legacy_id} sin property_type resolvible"))
                    continue

                # subtype por NAME (si no existe -> None, NO crear)
                pst_name = legacy_property_subtypes.get(int(legacy_property_subtype_id or 0))
                ps = pick_by_name(PropertySubtype.objects.all(), pst_name) or None

                if ps is None and not Property._meta.get_field("property_subtype").null:
                    raise RuntimeError(
                        "Tu modelo nuevo Property.property_subtype NO permite null. "
                        "Cámbialo a null=True, blank=True para poder migrar sin subtipo."
                    )

                # operation_type por NAME (si falla -> default Venta)
                op_name = legacy_operation_types.get(int(legacy_operation_type_id or 0))
                op = pick_by_name(OperationType.objects.all(), op_name) or OperationType.objects.filter(id=legacy_operation_type_id).first()
                if not op:
                    op = default_op

                # currency por NAME
                cur_name = legacy_currencies.get(int(legacy_currency_id or 0))
                cur = pick_by_name(Currency.objects.all(), cur_name) or Currency.objects.filter(id=legacy_currency_id).first()
                if not cur:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"[SKIP] legacy_id={legacy_id} sin currency resolvible"))
                    continue

                # payment_method por NAME (forma_de_pago legacy)
                pm_name = legacy_payment_methods.get(int(legacy_payment_method_id or 0))
                pm = pick_by_name(PaymentMethod.objects.all(), pm_name) or PaymentMethod.objects.filter(id=legacy_payment_method_id).first()
                if not pm:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"[SKIP] legacy_id={legacy_id} sin payment_method resolvible"))
                    continue

                # property_condition (new) = legacy.status (PropertyStatus legacy)
                legacy_prop_status_name = legacy_property_statuses.get(int(legacy_status_id or 0))
                prop_condition = pick_by_name(PropertyCondition.objects.all(), legacy_prop_status_name)

                # property_status (new) = availability_status legacy (y si no existe, CREARLO)
                av = (legacy_availability_status or "").strip().lower()
                desired_name = availability_to_name.get(av, legacy_availability_status)
                desired_name = norm(desired_name) or av or "Sin estado"
                prop_status = pick_by_name(PropertyStatus.objects.all(), desired_name)
                if not prop_status:
                    prop_status, _ = PropertyStatus.objects.get_or_create(name=desired_name)

                # district por NAME (AHORA OPCIONAL)
                dist_name = legacy_districts.get(int(legacy_district_id or 0))
                dist = (
                    pick_by_name(District.objects.all(), dist_name)
                    or District.objects.filter(id=legacy_district_id).first()
                )

                # antes: si no dist -> SKIP
                # ahora: si no dist -> None
                if not dist:
                    dist = None

                # urbanization por NAME (opcional)
                urb = None
                if legacy_urbanization_id:
                    urb_name = legacy_urbanizations.get(int(legacy_urbanization_id or 0))
                    urb = pick_by_name(Urbanization.objects.all(), urb_name) or Urbanization.objects.filter(id=legacy_urbanization_id).first()

                # responsible por username/email/etc
                legacy_resp_name = None
                if legacy_responsible_id:
                    legacy_resp_name = legacy_user_name_by_id.get(int(legacy_responsible_id), None)
                resp = resolve_responsible_user(User, legacy_responsible_id, legacy_resp_name)

                lat, lng = parse_coords(legacy_coordinates)
                prop_uuid = uuid.uuid5(uuid.NAMESPACE_URL, f"legacy-property-{legacy_id}")

                defaults = {
                    "contact": None,

                    "property_type": pt,
                    "property_subtype": ps,
                    "property_condition": prop_condition,
                    "operation_type": op,
                    "currency": cur,
                    "payment_method": pm,

                    "district": dist,
                    "urbanization": urb,

                    "property_status": prop_status,
                    "responsible": resp,

                    "wp_post_id": legacy_wp_post_id,
                    "wp_slug": legacy_wp_slug,
                    "wp_last_sync": make_aware_if_needed(legacy_wp_last_sync),

                    # no mapear proyectos
                    "is_project": False,
                    "project_name": None,

                    "uuid": prop_uuid,

                    # si vienen vacíos -> se quedan vacíos
                    "title": legacy_title or "",
                    "description": legacy_description or "",

                    # code
                    "code": legacy_code or "",

                    "price": to_decimal(legacy_price),

                    # no mapear maintenance_fee
                    "maintenance_fee": None,

                    "map_address": legacy_exact_address,
                    "display_address": legacy_real_address,

                    "latitude": lat,
                    "longitude": lng,

                    "registry_number": None,
                }

                if hasattr(Property, "is_active"):
                    defaults["is_active"] = bool(legacy_is_active)
                if hasattr(Property, "created_at"):
                    defaults["created_at"] = make_aware_if_needed(legacy_created_at)
                if hasattr(Property, "updated_at"):
                    defaults["updated_at"] = make_aware_if_needed(legacy_updated_at)

                _, was_created = Property.objects.update_or_create(
                    uuid=prop_uuid,
                    defaults=defaults,
                )

                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Migración properties OK | created={created} updated={updated} skipped={skipped}"
        ))