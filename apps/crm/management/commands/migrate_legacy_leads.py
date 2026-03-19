# apps/crm/management/commands/migrate_legacy_leads.py
from __future__ import annotations

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.utils import timezone


def norm(s):
    if s is None:
        return None
    s = str(s).strip()
    return s or None


def make_aware_if_needed(dt):
    if not dt:
        return None
    try:
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
    except Exception:
        pass
    return dt


def try_fetchall(cursor, sql: str):
    cursor.execute(sql)
    return cursor.fetchall()


def get_id_name_map(cursor, sql_candidates: list[str]) -> dict[int, str]:
    """
    Prueba varios SQLs (por nombres de tabla distintos) y retorna {id: name}.
    Si ninguno funciona, retorna {} sin romper la migración.
    """
    for sql in sql_candidates:
        try:
            rows = try_fetchall(cursor, sql)
            out = {}
            for _id, name in rows:
                try:
                    out[int(_id)] = str(name)
                except Exception:
                    continue
            if out:
                return out
            # si funcionó pero está vacío igual lo devolvemos
            return out
        except Exception:
            continue
    return {}


class Command(BaseCommand):
    help = "Migra Leads desde legacy.crm_leads hacia new.crm.Lead (por ids legacy + names en new)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")
        parser.add_argument("--limit", type=int, default=None, help="Limita filas (debug).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        # NEW MODELS
        LeadNew = apps.get_model("crm", "Lead")
        PropertyNew = apps.get_model("properties", "Property")
        User = apps.get_model("users", "User")

        LeadStatusNew = apps.get_model("catalogs", "LeadStatus")
        CanalLeadNew = apps.get_model("catalogs", "CanalLead")
        OperationTypeNew = apps.get_model("catalogs", "OperationType")

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración leads (legacy → new) =="))

        # ------------------------------------------------------------
        # 1) Leer leads base desde legacy (SIN JOIN a tablas desconocidas)
        # ------------------------------------------------------------
        sql = """
            SELECT
                l.id,
                l.username,
                l.full_name,
                l.phone,
                l.email,
                l.lead_status_id,
                l.canal_lead_id,
                l.notes,
                l.date_entry,
                l.id_chatwoot,
                l.date_last_message,
                l.user_last_message,
                l.is_active
            FROM crm_leads l
            ORDER BY l.id
        """
        if limit:
            sql += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        with connections["legacy"].cursor() as cursor:
            cursor.execute(sql)
            leads_rows = cursor.fetchall()

        self.stdout.write(f"Legacy leads: {len(leads_rows)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        # ------------------------------------------------------------
        # 2) Mapa legacy: lead_status_id -> name, canal_lead_id -> name
        #    (probamos varios nombres de tabla posibles)
        # ------------------------------------------------------------
        with connections["legacy"].cursor() as cursor:
            lead_status_map = get_id_name_map(
                cursor,
                [
                    "SELECT id, name FROM lead_status",
                    "SELECT id, name FROM lead_statuses",
                    "SELECT id, name FROM crm_lead_status",
                    "SELECT id, name FROM crm_lead_statuses",
                    "SELECT id, name FROM crm_leadstatus",
                    "SELECT id, name FROM crm_leadstatuses",
                ],
            )
            canal_lead_map = get_id_name_map(
                cursor,
                [
                    "SELECT id, name FROM canal_leads",
                    "SELECT id, name FROM canal_lead",
                    "SELECT id, name FROM canal_leads_types",
                    "SELECT id, name FROM crm_canal_lead",
                    "SELECT id, name FROM crm_canal_leads",
                    "SELECT id, name FROM crm_canallead",
                    "SELECT id, name FROM crm_canalleads",
                ],
            )

        # ------------------------------------------------------------
        # 3) Pre-cargar M2M legacy en mapas (si fallan, no rompe)
        # ------------------------------------------------------------
        sql_assigned_candidates = [
            # nombres comunes
            "SELECT lead_id, u.username, u.email, u.id FROM crm_leads_assigned_to la INNER JOIN users_user u ON u.id = la.user_id",
            "SELECT lead_id, u.username, u.email, u.id FROM crm_leads_assigned_to la INNER JOIN auth_user u ON u.id = la.user_id",
            "SELECT lead_id, u.username, u.email, u.id FROM crm_lead_assigned_to la INNER JOIN users_user u ON u.id = la.user_id",
        ]

        sql_ops_candidates = [
            "SELECT lead_id, ot.name FROM crm_leads_operation_types lo INNER JOIN operation_types ot ON ot.id = lo.operationtype_id",
            "SELECT lead_id, ot.name FROM crm_leads_operation_types lo INNER JOIN operation_types ot ON ot.id = lo.operation_type_id",
            "SELECT lead_id, ot.name FROM crm_lead_operation_types lo INNER JOIN operation_types ot ON ot.id = lo.operationtype_id",
        ]

        sql_props_candidates = [
            "SELECT lead_id, p.code FROM crm_leads_properties lp INNER JOIN properties p ON p.id = lp.property_id",
            "SELECT lead_id, p.code FROM crm_lead_properties lp INNER JOIN properties p ON p.id = lp.property_id",
        ]

        lead_assigned_map = {}
        lead_ops_map = {}
        lead_props_map = {}

        with connections["legacy"].cursor() as cursor:
            # assigned
            for sql_a in sql_assigned_candidates:
                try:
                    cursor.execute(sql_a)
                    for lead_id, uname, email, uid in cursor.fetchall():
                        lead_assigned_map.setdefault(int(lead_id), []).append((uname, email, uid))
                    break
                except Exception:
                    continue

            # ops
            for sql_o in sql_ops_candidates:
                try:
                    cursor.execute(sql_o)
                    for lead_id, op_name in cursor.fetchall():
                        lead_ops_map.setdefault(int(lead_id), []).append(op_name)
                    break
                except Exception:
                    continue

            # props
            for sql_p in sql_props_candidates:
                try:
                    cursor.execute(sql_p)
                    for lead_id, code in cursor.fetchall():
                        lead_props_map.setdefault(int(lead_id), []).append(code)
                    break
                except Exception:
                    continue

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for (
                legacy_id,
                username,
                full_name,
                phone,
                email,
                lead_status_id,
                canal_lead_id,
                notes,
                date_entry,
                id_chatwoot,
                date_last_message,
                user_last_message,
                is_active,
            ) in leads_rows:
                legacy_id = int(legacy_id)

                username = norm(username)
                phone = norm(phone)
                email = norm(email)
                full_name = norm(full_name) or ""  # en tu modelo nuevo full_name es requerido

                # --------------------
                # assigned_to (legacy M2M -> new FK)
                # --------------------
                assigned_to = None
                candidates = lead_assigned_map.get(legacy_id, [])
                if candidates:
                    uname, uemail, uid = candidates[0]
                    uname = norm(uname)
                    uemail = norm(uemail)

                    if uname:
                        assigned_to = User.objects.filter(username__iexact=uname).first()
                    if not assigned_to and uemail:
                        assigned_to = User.objects.filter(email__iexact=uemail).first()
                    if not assigned_to and uid:
                        assigned_to = User.objects.filter(id=int(uid)).first()

                # --------------------
                # lead_status / canal_lead por NAME (desde mapas legacy)
                # --------------------
                ls_obj = None
                if lead_status_id is not None:
                    ls_name = norm(lead_status_map.get(int(lead_status_id)))
                    if ls_name:
                        ls_obj = LeadStatusNew.objects.filter(name__iexact=ls_name).first()

                cl_obj = None
                if canal_lead_id is not None:
                    cl_name = norm(canal_lead_map.get(int(canal_lead_id)))
                    if cl_name:
                        cl_obj = CanalLeadNew.objects.filter(name__iexact=cl_name).first()

                # --------------------
                # lookup idempotente (prioriza id_chatwoot)
                # --------------------
                lookup = {}
                if norm(id_chatwoot):
                    lookup["id_chatwoot"] = norm(id_chatwoot)
                else:
                    lookup["username"] = username
                    lookup["phone"] = phone

                if not any(lookup.values()):
                    self.stdout.write(self.style.WARNING(f"[SKIP] legacy_id={legacy_id} sin username/phone/id_chatwoot"))
                    skipped += 1
                    continue

                defaults = {
                    "contact": None,
                    "assigned_to": assigned_to,
                    "area": None,

                    # estos campos en tu cruce: si no hay, deben quedar null
                    "lead_status": ls_obj,
                    "canal_lead": cl_obj,

                    "source_detail": None,

                    "full_name": full_name,
                    "phone": phone,
                    "email": email,
                    "notes": norm(notes),
                    "username": username,

                    "date_entry": make_aware_if_needed(date_entry),
                    "id_chatwoot": norm(id_chatwoot),
                    "date_last_message": make_aware_if_needed(date_last_message),
                    "user_last_message": norm(user_last_message),

                    "is_active": bool(is_active),
                }

                obj, was_created = LeadNew.objects.update_or_create(defaults=defaults, **lookup)

                # --------------------
                # M2M: operation_types (por name)
                # --------------------
                op_names = lead_ops_map.get(legacy_id, [])
                if op_names:
                    op_objs = []
                    for n in op_names:
                        n2 = norm(n)
                        if not n2:
                            continue
                        op = OperationTypeNew.objects.filter(name__iexact=n2).first()
                        if op:
                            op_objs.append(op)
                    obj.operation_types.set(op_objs) if op_objs else obj.operation_types.clear()

                # --------------------
                # M2M: properties (por code)
                # --------------------
                prop_codes = lead_props_map.get(legacy_id, [])
                if prop_codes:
                    prop_objs = []
                    for code in prop_codes:
                        c = norm(code)
                        if not c:
                            continue
                        p = PropertyNew.objects.filter(code=c).first()
                        if p:
                            prop_objs.append(p)
                    obj.properties.set(prop_objs) if prop_objs else obj.properties.clear()

                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Migración leads OK | created={created} updated={updated} skipped={skipped}"
            )
        )