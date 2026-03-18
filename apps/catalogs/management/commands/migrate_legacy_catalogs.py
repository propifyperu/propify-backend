# apps/catalogs/management/commands/migrate_legacy_catalogs.py
from django.core.management.base import BaseCommand
from django.db import connections, transaction

from apps.catalogs.models import (
    CanalLead,
    Currency,
    DocumentType,
    EventType,
    LeadStatus,
    OperationType,
    PaymentMethod,
    PropertyCondition,
    PropertyStatus,
    PropertySubtype,
    PropertyType,
    UtilityService,
)


class Command(BaseCommand):
    help = "Migra catálogos desde legacy (Azure SQL) hacia la DB nueva."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración catalogs (legacy → new) =="))

        # Maps legacy_id -> new_obj (solo necesarios donde hay FK)
        prop_type_map = {}

        with connections["legacy"].cursor() as cursor:
            # 1:1 simples
            cursor.execute("SELECT id, name, is_active FROM canal_leads")
            legacy_canal_leads = cursor.fetchall()
            self.stdout.write(f"CanalLead legacy: {len(legacy_canal_leads)}")

            cursor.execute("SELECT id, code, name, symbol, is_active FROM currencies")
            legacy_currencies = cursor.fetchall()
            self.stdout.write(f"Currency legacy: {len(legacy_currencies)}")

            cursor.execute("SELECT id, code, name, is_active FROM document_types")
            legacy_document_types = cursor.fetchall()
            self.stdout.write(f"DocumentType legacy: {len(legacy_document_types)}")

            cursor.execute("SELECT id, name, is_active FROM event_types")
            legacy_event_types = cursor.fetchall()
            self.stdout.write(f"EventType legacy: {len(legacy_event_types)}")

            cursor.execute("SELECT id, name, is_active FROM crm_lead_statuses")
            legacy_lead_statuses = cursor.fetchall()
            self.stdout.write(f"LeadStatus legacy: {len(legacy_lead_statuses)}")

            cursor.execute("SELECT id, name, is_active FROM operation_types")
            legacy_operation_types = cursor.fetchall()
            self.stdout.write(f"OperationType legacy: {len(legacy_operation_types)}")

            cursor.execute("SELECT id, name, is_active FROM payment_methods")
            legacy_payment_methods = cursor.fetchall()
            self.stdout.write(f"PaymentMethod legacy: {len(legacy_payment_methods)}")

            # PropertyCondition new = PropertyStatus legacy (estreno/antiguedad/en construccion)
            cursor.execute("SELECT id, name, is_active FROM property_statuses")
            legacy_property_conditions = cursor.fetchall()
            self.stdout.write(f"PropertyCondition(legacy property_statuses): {len(legacy_property_conditions)}")

            # PropertyStatus new: NO existe en legacy -> valores fijos
            new_property_statuses = ["Draft", "Captacion", "Disponible", "Reservada", "Pausada", "No disponible"]
            self.stdout.write(f"PropertyStatus(new fixed): {len(new_property_statuses)}")

            # PropertyType/Subtype
            cursor.execute("SELECT id, name, is_active FROM property_types")
            legacy_property_types = cursor.fetchall()
            self.stdout.write(f"PropertyType legacy: {len(legacy_property_types)}")

            cursor.execute("SELECT id, property_type_id, name, is_active FROM property_subtypes")
            legacy_property_subtypes = cursor.fetchall()
            self.stdout.write(f"PropertySubtype legacy: {len(legacy_property_subtypes)}")

            # UtilityService merge 4 tablas
            cursor.execute("SELECT id, name, is_active FROM water_service_types")
            legacy_water = cursor.fetchall()
            self.stdout.write(f"WaterServiceType legacy: {len(legacy_water)}")

            cursor.execute("SELECT id, name, is_active FROM energy_service_types")
            legacy_energy = cursor.fetchall()
            self.stdout.write(f"EnergyServiceType legacy: {len(legacy_energy)}")

            cursor.execute("SELECT id, name, is_active FROM drainage_service_types")
            legacy_drainage = cursor.fetchall()
            self.stdout.write(f"DrainageServiceType legacy: {len(legacy_drainage)}")

            cursor.execute("SELECT id, name, is_active FROM gas_service_types")
            legacy_gas = cursor.fetchall()
            self.stdout.write(f"GasServiceType legacy: {len(legacy_gas)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        with transaction.atomic():
            # 1) CanalLead
            for legacy_id, name, is_active in legacy_canal_leads:
                CanalLead.objects.update_or_create(
                    name=str(name).strip(),
                    defaults={"is_active": bool(is_active)},
                )

            # 2) Currency (unique: code)
            for legacy_id, code, name, symbol, is_active in legacy_currencies:
                Currency.objects.update_or_create(
                    code=str(code).strip(),
                    defaults={
                        "name": str(name).strip(),
                        "symbol": (str(symbol).strip() if symbol is not None else None),
                        "is_active": bool(is_active),
                    },
                )

            # 3) DocumentType (unique: code)
            for legacy_id, code, name, is_active in legacy_document_types:
                code = (str(code).strip() if code else "")
                if not code:
                    self.stdout.write(self.style.WARNING(f"DocumentType legacy id={legacy_id} sin code, skip"))
                    continue

                DocumentType.objects.update_or_create(
                    code=code,
                    defaults={"name": str(name).strip(), "is_active": bool(is_active)},
                )

            # 4) EventType (BaseModel: name + is_active)
            for legacy_id, name, is_active in legacy_event_types:
                EventType.objects.update_or_create(
                    name=str(name).strip(),
                    defaults={"is_active": bool(is_active)},
                )

            # 5) LeadStatus (BaseModel)
            for legacy_id, name, is_active in legacy_lead_statuses:
                LeadStatus.objects.update_or_create(
                    name=str(name).strip(),
                    defaults={"is_active": bool(is_active)},
                )

            # 6) OperationType (BaseModel)
            for legacy_id, name, is_active in legacy_operation_types:
                OperationType.objects.update_or_create(
                    name=str(name).strip(),
                    defaults={"is_active": bool(is_active)},
                )

            # 7) PaymentMethod (BaseModel)
            for legacy_id, name, is_active in legacy_payment_methods:
                PaymentMethod.objects.update_or_create(
                    name=str(name).strip(),
                    defaults={"is_active": bool(is_active)},
                )

            # 8) PropertyCondition new = property_statuses legacy
            for legacy_id, name, is_active in legacy_property_conditions:
                PropertyCondition.objects.update_or_create(
                    name=str(name).strip(),
                    defaults={"is_active": bool(is_active)},
                )

            # 9) PropertyStatus new (fijo)
            for name in new_property_statuses:
                PropertyStatus.objects.update_or_create(
                    name=name,
                    defaults={"is_active": True},
                )

            # 10) PropertyType (BaseModel) + map legacy_id -> obj
            for legacy_id, name, is_active in legacy_property_types:
                obj, _ = PropertyType.objects.update_or_create(
                    name=str(name).strip(),
                    defaults={"is_active": bool(is_active)},
                )
                prop_type_map[int(legacy_id)] = obj

            # 11) PropertySubtype (FK property_type + name)
            for legacy_id, legacy_type_id, name, is_active in legacy_property_subtypes:
                pt = prop_type_map.get(int(legacy_type_id))
                if not pt:
                    self.stdout.write(
                        self.style.WARNING(
                            f"PropertySubtype {legacy_id} sin property_type {legacy_type_id}, skip"
                        )
                    )
                    continue

                PropertySubtype.objects.update_or_create(
                    property_type=pt,
                    name=str(name).strip(),
                    defaults={"is_active": bool(is_active)},
                )

            # 12) UtilityService (merge 4 tablas)
            def upsert_utility(rows, category: str):
                for legacy_id, name, is_active in rows:
                    UtilityService.objects.update_or_create(
                        category=category,
                        name=str(name).strip(),
                        defaults={"is_active": bool(is_active)},
                    )

            upsert_utility(legacy_water, "Agua")
            upsert_utility(legacy_energy, "Luz")
            upsert_utility(legacy_drainage, "Drenaje")
            upsert_utility(legacy_gas, "Gas")

        self.stdout.write(self.style.SUCCESS("✅ Migración catalogs terminada OK"))