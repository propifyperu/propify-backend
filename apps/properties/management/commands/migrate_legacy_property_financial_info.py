# apps/properties/management/commands/migrate_legacy_property_financial_info.py
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connections, transaction


def to_decimal(val):
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return None


def normalize_contract_type(choice_label: str | None) -> str | None:
    """
    Legacy trae ContractType.name (ej: 'Exclusivo', 'Semi exclusivo', 'No exclusivo').
    En new guardamos el VALUE del choice: exclusive / semi_exclusive / non_exclusive
    usando el label humano como puente.
    """
    if not choice_label:
        return None

    n = " ".join(str(choice_label).strip().split()).lower()

    if n == "exclusivo":
        return "exclusive"
    if n in {"semi exclusivo", "semiexclusivo", "semi-exclusivo", "semi_exclusivo"}:
        return "semi_exclusive"
    if n in {"no exclusivo", "no-exclusivo", "no_exclusivo", "non exclusivo"}:
        return "non_exclusive"

    return None


class Command(BaseCommand):
    help = "Migra PropertyFinancialInfo desde legacy.property_financial_info hacia new.PropertyFinancialInfo (por Property.code)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")
        parser.add_argument("--limit", type=int, default=None, help="Limita cantidad de filas (debug).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        Property = apps.get_model("properties", "Property")  # new
        FinancialNew = apps.get_model("properties", "PropertyFinancialInfo")  # new

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración property_financial_info (legacy → new) =="))

        sql = """
            SELECT
                p.code AS property_code,
                pfi.initial_commission_percentage,
                pfi.final_commission_percentage,
                ct.name AS contract_type_name,
                ns.name AS negotiation_status_name
            FROM property_financial_info pfi
            INNER JOIN properties p ON p.id = pfi.property_id
            LEFT JOIN contract_types ct ON ct.id = pfi.contract_type_id
            LEFT JOIN negotiation_statuses ns ON ns.id = pfi.negotiation_status_id
            ORDER BY p.id, pfi.property_id
        """
        if limit:
            sql += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        with connections["legacy"].cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        self.stdout.write(f"Legacy property_financial_info: {len(rows)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for (
                property_code,
                initial_commission_percentage,
                final_commission_percentage,
                contract_type_name,
                negotiation_status_name,
            ) in rows:
                if not property_code:
                    skipped += 1
                    continue

                prop = Property.objects.filter(code=property_code).first()
                if not prop:
                    self.stdout.write(self.style.WARNING(f"[SKIP] code={property_code} no existe en new.Property"))
                    skipped += 1
                    continue

                contract_value = normalize_contract_type(contract_type_name)
                if contract_type_name and not contract_value:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[WARN] code={property_code} contract_type='{contract_type_name}' no calza con choices -> NULL"
                        )
                    )

                negotiation_status = (negotiation_status_name or "").strip() or None

                defaults = {
                    "commission_initial": to_decimal(initial_commission_percentage),
                    "commission_final": to_decimal(final_commission_percentage),
                    "commission_pf": None,  # NUEVO -> NULL
                    "contract_type": contract_value,  # choice value o None
                    "negotiation_status": negotiation_status,
                    "notes": None,  # NUEVO -> NULL
                }

                obj, was_created = FinancialNew.objects.update_or_create(
                    property=prop,
                    defaults=defaults,
                )

                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Migración property_financial_info OK | created={created} updated={updated} skipped={skipped}"
            )
        )