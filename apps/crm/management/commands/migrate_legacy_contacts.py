# apps/crm/management/commands/migrate_legacy_contacts.py
from __future__ import annotations

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections, transaction


def norm(s: str | None) -> str:
    return " ".join(str(s or "").strip().split())


def key_name(fn: str | None, ln: str | None) -> str:
    return f"{norm(fn)} {norm(ln)}".strip().lower()


def is_bad_name(k: str) -> bool:
    kk = (k or "").replace(" ", "")
    return (not kk) or (kk == "sinnombre")


def clean_photo_path(path: str | None) -> str | None:
    if not path:
        return None
    p = str(path).strip().replace("\\", "/")
    marker = "owners/photos/"
    idx = p.find(marker)
    if idx >= 0:
        return p[idx:]
    return p


def normalize_document_type(doc_type_name: str | None) -> str | None:
    if not doc_type_name:
        return None
    n = norm(doc_type_name).lower()
    if n == "dni":
        return "dni"
    if n in {"passport", "pasaporte"}:
        return "passport"
    if n in {"ce", "c.e."} or ("carnet" in n and "extran" in n):
        return "ce"
    return None


def maybe_decrypt(val):
    """
    Intenta desencriptar strings tipo 'gAAAAA...' (Fernet).
    Si tu repo tiene un util de decrypt, úsalo aquí.
    Si no existe, devuelve el valor original (quedará encriptado).
    """
    if val is None:
        return None
    s = str(val)

    # Heurística: ciphertext típico Fernet empieza con "gAAAAA"
    if not s.startswith("gAAAAA"):
        return s

    # ✅ Opción 1: si tienes algo tipo common.crypto.decrypt(...)
    # Ajusta este import al path REAL de tu repo si existe.
    try:
        from common.crypto import decrypt_value  # <-- si existe en tu repo

        return decrypt_value(s)
    except Exception:
        pass

    # ✅ Opción 2: si guardaste una key Fernet en settings (ej: FIELD_ENCRYPTION_KEY)
    # y tienes cryptography instalado, intenta desencriptar directo.
    try:
        from cryptography.fernet import Fernet

        key = getattr(settings, "FIELD_ENCRYPTION_KEY", None) or getattr(settings, "ENCRYPTION_KEY", None)
        if not key:
            return s
        f = Fernet(key)
        return f.decrypt(s.encode("utf-8")).decode("utf-8")
    except Exception:
        return s


class Command(BaseCommand):
    help = "Migra Contacts desde legacy.property_owners hacia crm.Contact (dedupe + skip Sin nombre)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        Contact = apps.get_model("crm", "Contact")

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración contacts (legacy SQL → new) =="))

        sql = """
            SELECT
                po.id,
                po.first_name,
                po.last_name,
                dt.name AS document_type_name,
                po.document_number,
                po.birth_date,
                po.gender,
                po.phone,
                po.email,
                po.photo,
                po.is_active
            FROM property_owners po
            LEFT JOIN document_types dt ON dt.id = po.document_type_id
            ORDER BY po.id
        """
        if limit:
            sql += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        with connections["legacy"].cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        self.stdout.write(f"Legacy owners: {len(rows)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado"))
            return

        created = 0
        skipped = 0
        seen: set[str] = set()

        with transaction.atomic():
            for (
                _legacy_id,
                first_name,
                last_name,
                document_type_name,
                document_number,
                birth_date,
                gender,
                phone,
                email,
                photo,
                is_active,
            ) in rows:
                fn = norm(maybe_decrypt(first_name)) or None
                ln = norm(maybe_decrypt(last_name)) or None

                k = key_name(fn, ln)
                if is_bad_name(k):
                    skipped += 1
                    continue

                if k in seen:
                    skipped += 1
                    continue
                seen.add(k)

                # si ya existe en new por nombre, no duplicamos
                if Contact.objects.filter(first_name__iexact=fn or "", last_name__iexact=ln or "").exists():
                    skipped += 1
                    continue

                doc_value = normalize_document_type(maybe_decrypt(document_type_name))

                defaults = {
                    "assigned_agent": None,
                    "first_name": fn,
                    "last_name": ln,
                    "document_type": doc_value,
                    "document_number": norm(maybe_decrypt(document_number)) or None,
                    "birth_date": birth_date,
                    "gender": gender if gender in ("M", "F", "O") else None,
                    "phone": norm(maybe_decrypt(phone)) or None,
                    "email": norm(maybe_decrypt(email)) or None,
                    "photo": clean_photo_path(str(photo) if photo else None),
                    # contact_type queda default=other
                    "is_active": bool(is_active),
                }

                Contact.objects.create(**defaults)
                created += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Contacts OK | created={created} skipped={skipped}"))