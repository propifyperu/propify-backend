# apps/properties/management/commands/migrate_legacy_property_media.py
from __future__ import annotations

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connections, transaction


def clean_name(path: str | None) -> str | None:
    """
    Normaliza el .name del FileField:
    - quita backslashes
    - intenta quedarse con la parte relativa del storage si viniera con algo extra
    """
    if not path:
        return None
    p = str(path).strip().replace("\\", "/")
    for marker in ("properties/images/", "properties/videos/"):
        idx = p.find(marker)
        if idx >= 0:
            return p[idx:]
    return p


class Command(BaseCommand):
    help = "Migra PropertyMedia desde legacy PropertyImage/PropertyVideo hacia new.PropertyMedia (por Property.code)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")
        parser.add_argument("--limit", type=int, default=None, help="Limita cantidad de filas (debug).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        Property = apps.get_model("properties", "Property")           # new
        PropertyMedia = apps.get_model("properties", "PropertyMedia") # new

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración property_media (legacy → new) =="))

        # 1) Leer legacy IMAGES
        sql_images = """
            SELECT
                p.code          AS property_code,
                pi.image        AS image_path,
                pi.[order]      AS image_order,
                pi.wp_media_id  AS wp_media_id,
                pi.wp_source_url AS wp_source_url,
                pi.wp_last_sync AS wp_last_sync
            FROM property_images pi
            INNER JOIN properties p ON p.id = pi.property_id
            ORDER BY p.id, pi.[order], pi.id
        """
        if limit:
            sql_images += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        # 2) Leer legacy VIDEOS
        sql_videos = """
            SELECT
                p.code     AS property_code,
                pv.video   AS video_path,
                pv.title   AS video_title
            FROM property_videos pv
            INNER JOIN properties p ON p.id = pv.property_id
            ORDER BY p.id, pv.id
        """
        if limit:
            sql_videos += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        with connections["legacy"].cursor() as cursor:
            cursor.execute(sql_images)
            images = cursor.fetchall()

            cursor.execute(sql_videos)
            videos = cursor.fetchall()

        self.stdout.write(f"Legacy images: {len(images)} | Legacy videos: {len(videos)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            # ---------- IMAGES ----------
            for (property_code, image_path, image_order, wp_media_id, wp_source_url, wp_last_sync) in images:
                if not property_code:
                    skipped += 1
                    continue

                prop = Property.objects.filter(code=property_code).first()
                if not prop:
                    self.stdout.write(self.style.WARNING(f"[SKIP] image code={property_code} no existe en new.Property"))
                    skipped += 1
                    continue

                file_name = clean_name(image_path)
                if not file_name:
                    skipped += 1
                    continue

                defaults = {
                    "media_type": "image",
                    "file": file_name,  # solo ruta existente
                    "title": None,       # para images vacío
                    "label": None,
                    "order": int(image_order or 0),
                    "wp_media_id": wp_media_id,
                    "wp_source_url": wp_source_url,
                    "wp_last_sync": wp_last_sync,
                }

                obj, was_created = PropertyMedia.objects.update_or_create(
                    property=prop,
                    media_type="image",
                    file=file_name,
                    defaults=defaults,
                )

                created += 1 if was_created else 0
                updated += 0 if was_created else 1

            # ---------- VIDEOS ----------
            for (property_code, video_path, video_title) in videos:
                if not property_code:
                    skipped += 1
                    continue

                prop = Property.objects.filter(code=property_code).first()
                if not prop:
                    self.stdout.write(self.style.WARNING(f"[SKIP] video code={property_code} no existe en new.Property"))
                    skipped += 1
                    continue

                file_name = clean_name(video_path)
                if not file_name:
                    skipped += 1
                    continue

                defaults = {
                    "media_type": "video",
                    "file": file_name,
                    "title": (video_title or "").strip() or None,
                    "label": None,
                    "order": 0,  # legacy no tiene order en videos
                    "wp_media_id": None,
                    "wp_source_url": None,
                    "wp_last_sync": None,
                }

                obj, was_created = PropertyMedia.objects.update_or_create(
                    property=prop,
                    media_type="video",
                    file=file_name,
                    defaults=defaults,
                )

                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Migración property_media OK | created={created} updated={updated} skipped={skipped}"
            )
        )