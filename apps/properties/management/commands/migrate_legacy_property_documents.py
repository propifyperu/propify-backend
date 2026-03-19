# apps/properties/management/commands/migrate_legacy_property_documents.py
from __future__ import annotations

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connections, transaction


def clean_name(path: str | None) -> str | None:
    if not path:
        return None
    p = str(path).strip().replace("\\", "/")
    marker = "properties/documents/"
    idx = p.find(marker)
    if idx >= 0:
        return p[idx:]
    return p


class Command(BaseCommand):
    help = "Migra PropertyDocument desde legacy.property_documents hacia new.PropertyDocument (por Property.code)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")
        parser.add_argument("--limit", type=int, default=None, help="Limita cantidad de filas (debug).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        Property = apps.get_model("properties", "Property")  # new
        PropertyDocumentNew = apps.get_model("properties", "PropertyDocument")  # new
        DocumentType = apps.get_model("catalogs", "DocumentType")  # new catalog

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración property_document (legacy → new) =="))

        sql = """
            SELECT
                p.code AS property_code,
                dt.name AS document_type_name,
                pd.[file] AS file_path,
                pd.valid_from,
                pd.valid_to,
                pd.is_approved,
                pd.description
            FROM property_documents pd
            INNER JOIN properties p ON p.id = pd.property_id
            LEFT JOIN document_types dt ON dt.id = pd.document_type_id
            ORDER BY p.id, pd.id
        """
        if limit:
            sql += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        with connections["legacy"].cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        self.stdout.write(f"Legacy property_documents: {len(rows)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for (
                property_code,
                document_type_name,
                file_path,
                valid_from,
                valid_to,
                is_approved,
                description,
            ) in rows:
                if not property_code:
                    skipped += 1
                    continue

                prop = Property.objects.filter(code=property_code).first()
                if not prop:
                    self.stdout.write(self.style.WARNING(f"[SKIP] code={property_code} no existe en new.Property"))
                    skipped += 1
                    continue

                dt_obj = None
                dt_name = (document_type_name or "").strip()
                if dt_name:
                    dt_obj = DocumentType.objects.filter(name__iexact=dt_name).first()
                    if not dt_obj:
                        # Si el tipo vino pero no existe en new, lo dejamos null (no reventamos)
                        self.stdout.write(
                            self.style.WARNING(
                                f"[WARN] code={property_code} document_type '{dt_name}' no existe en new -> se guardará NULL"
                            )
                        )
                        dt_obj = None

                file_name = clean_name(file_path)

                status = "approved" if bool(is_approved) else "pending"
                notes = (description or "").strip() or None

                defaults = {
                    "file": file_name,     # puede ser None si legacy no tiene file
                    "valid_from": valid_from,
                    "valid_to": valid_to,
                    "status": status,
                    "notes": notes,
                }

                # Si document_type es NULL, NO podemos usar update_or_create con esa "unicidad"
                # porque podrías tener múltiples docs sin tipo por property.
                # Entonces: creamos siempre uno nuevo si dt_obj is None.
                if dt_obj is None:
                    PropertyDocumentNew.objects.create(
                        property=prop,
                        document_type=None,
                        **defaults,
                    )
                    created += 1
                    continue

                obj, was_created = PropertyDocumentNew.objects.update_or_create(
                    property=prop,
                    document_type=dt_obj,
                    defaults=defaults,
                )
                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Migración property_document OK | created={created} updated={updated} skipped={skipped}"
            )
        )