# apps/locations/management/commands/migrate_legacy_locations.py
from django.core.management.base import BaseCommand
from django.db import connections, transaction

from apps.locations.models import Country, Department, Province, District, Urbanization


class Command(BaseCommand):
    help = "Migra ubicaciones desde legacy (Azure SQL) hacia la DB nueva."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")
        parser.add_argument("--peru-code", default="PER")
        parser.add_argument("--peru-name", default="Perú")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        peru_code = options["peru_code"]
        peru_name = options["peru_name"]

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración locations (legacy → new) =="))

        # 1) Asegurar Country Perú
        if dry_run:
            peru = Country(code=peru_code, name=peru_name, is_active=True)
        else:
            peru, _ = Country.objects.update_or_create(
                code=peru_code,
                defaults={"name": peru_name, "is_active": True},
            )

        # Maps legacy_id -> new_obj
        dept_map = {}
        prov_map = {}
        dist_map = {}

        with connections["legacy"].cursor() as cursor:
            # ---- Departments
            cursor.execute("SELECT id, name, is_active FROM properties_department")
            legacy_departments = cursor.fetchall()

            self.stdout.write(f"Departments legacy: {len(legacy_departments)}")

            # ---- Provinces
            cursor.execute("SELECT id, name, department_id, is_active FROM properties_province")
            legacy_provinces = cursor.fetchall()

            self.stdout.write(f"Provinces legacy: {len(legacy_provinces)}")

            # ---- Districts
            cursor.execute("SELECT id, name, province_id, is_active FROM properties_district")
            legacy_districts = cursor.fetchall()

            self.stdout.write(f"Districts legacy: {len(legacy_districts)}")

            # ---- Urbanizations
            cursor.execute("SELECT id, name, district_id, is_active FROM properties_urbanization")
            legacy_urbanizations = cursor.fetchall()

            self.stdout.write(f"Urbanizations legacy: {len(legacy_urbanizations)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        with transaction.atomic():
            # 2) Migrar Departments (unique: country+name)
            for legacy_id, name, is_active in legacy_departments:
                obj, _ = Department.objects.update_or_create(
                    country=peru,
                    name=name.strip(),
                    defaults={"is_active": bool(is_active)},
                )
                dept_map[int(legacy_id)] = obj

            # 3) Migrar Provinces (unique: department+name)
            for legacy_id, name, department_id, is_active in legacy_provinces:
                dep = dept_map.get(int(department_id))
                if not dep:
                    # si por alguna razón falta el dept, lo saltamos con warning
                    self.stdout.write(self.style.WARNING(f"Province {legacy_id} sin department {department_id}, skip"))
                    continue

                obj, _ = Province.objects.update_or_create(
                    department=dep,
                    name=name.strip(),
                    defaults={"is_active": bool(is_active)},
                )
                prov_map[int(legacy_id)] = obj

            # 4) Migrar Districts (unique: province+name)
            for legacy_id, name, province_id, is_active in legacy_districts:
                prov = prov_map.get(int(province_id))
                if not prov:
                    self.stdout.write(self.style.WARNING(f"District {legacy_id} sin province {province_id}, skip"))
                    continue

                obj, _ = District.objects.update_or_create(
                    province=prov,
                    name=name.strip(),
                    defaults={"is_active": bool(is_active)},
                )
                dist_map[int(legacy_id)] = obj

            # 5) Migrar Urbanizations (unique: district+name)
            for legacy_id, name, district_id, is_active in legacy_urbanizations:
                dist = dist_map.get(int(district_id))
                if not dist:
                    self.stdout.write(self.style.WARNING(f"Urbanization {legacy_id} sin district {district_id}, skip"))
                    continue

                Urbanization.objects.update_or_create(
                    district=dist,
                    name=name.strip(),
                    defaults={"is_active": bool(is_active)},
                )

        self.stdout.write(self.style.SUCCESS("✅ Migración locations terminada OK"))