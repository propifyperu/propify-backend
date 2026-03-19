# apps/crm/management/commands/migrate_legacy_events.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.db.models import Q
from django.utils import timezone


def norm(s: str | None) -> str | None:
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    return " ".join(s.split())


def make_aware_if_needed(dt):
    if not dt:
        return dt
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def combine_date_time(d, t):
    if not d or not t:
        return None
    try:
        return make_aware_if_needed(datetime.combine(d, t))
    except Exception:
        return None


def normalize_phone(p: str | None) -> str | None:
    if not p:
        return None
    s = "".join(ch for ch in str(p) if ch.isdigit() or ch == "+")
    return s or None


def resolve_user_by_fullname(User, legacy_fullname: str | None):
    """
    legacy_fullname viene como: "Nombre Apellido Apellido" (o variantes).
    Se resuelve contra new users.User usando first_name + last_name.

    Estrategia:
    1) Exacto: first=primera palabra, last=resto completo
    2) last_name contiene (icontains) el resto
    3) fallback: username/email exactos (por si guardaron eso)
    """
    fn = norm(legacy_fullname)
    if not fn:
        return None

    # si te guardaron username/email en esa columna, lo rescatamos
    u = User.objects.filter(username__iexact=fn).first()
    if u:
        return u
    u = User.objects.filter(email__iexact=fn).first()
    if u:
        return u

    parts = fn.split(" ")
    if len(parts) >= 2:
        first = parts[0]
        last = " ".join(parts[1:])

        # exacto
        u = User.objects.filter(first_name__iexact=first, last_name__iexact=last).first()
        if u:
            return u

        # last_name contiene el resto (por variaciones / doble apellido / etc.)
        u = User.objects.filter(first_name__iexact=first, last_name__icontains=last).first()
        if u:
            return u

        # si el last tiene varias palabras, intentamos que last_name contenga TODAS
        qs = User.objects.filter(first_name__iexact=first)
        for token in [p for p in last.split(" ") if p]:
            qs = qs.filter(last_name__icontains=token)
        u = qs.first()
        if u:
            return u

    # último fallback: match flojo por contiene (por si te guardaron solo apellido o solo nombre)
    u = User.objects.filter(
        Q(first_name__iexact=fn) | Q(last_name__iexact=fn)
    ).first()
    return u


def resolve_contact_by_fullname(Contact, full_name: str | None):
    n = norm(full_name)
    if not n or n.lower() == "sin nombre":
        return None

    parts = n.split(" ")
    if len(parts) >= 2:
        first = parts[0]
        last = " ".join(parts[1:])
        c = Contact.objects.filter(first_name__iexact=first, last_name__iexact=last).first()
        if c:
            return c

        c = Contact.objects.filter(first_name__iexact=first, last_name__icontains=last).first()
        if c:
            return c

    c = Contact.objects.filter(first_name__iexact=n).first()
    if c:
        return c

    c = Contact.objects.filter(last_name__iexact=n).first()
    return c


class Command(BaseCommand):
    help = "Migra events desde legacy.events hacia new.crm.Event."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")
        parser.add_argument("--limit", type=int, default=None, help="Limita cantidad de filas (debug).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        EventNew = apps.get_model("crm", "Event")
        EventTypeNew = apps.get_model("catalogs", "EventType")
        PropertyNew = apps.get_model("properties", "Property")
        LeadNew = apps.get_model("crm", "Lead")
        ContactNew = apps.get_model("crm", "Contact")
        User = apps.get_model("users", "User")

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración events (legacy → new) =="))

        # OJO: usamos TRY_CONVERT para que si assigned_agent_id tiene texto, no reviente el JOIN
        sql = """
            SELECT
                e.id,
                e.code,
                et.name AS event_type_name,

                cu.username AS assigned_agent_username,
                (RTRIM(LTRIM(COALESCE(cu.first_name,''))) + ' ' + RTRIM(LTRIM(COALESCE(cu.last_name,'')))) AS assigned_agent_fullname,

                p.code AS property_code,

                l.phone AS lead_phone,

                (RTRIM(LTRIM(COALESCE(po.first_name,''))) + ' ' + RTRIM(LTRIM(COALESCE(po.last_name,'')))) AS contact_fullname,
                e.interesado AS interesado_fallback,

                e.titulo,
                e.detalle,
                e.seguimiento,

                e.fecha_evento,
                e.hora_inicio,
                e.hora_fin,

                e.status,
                e.is_active
            FROM events e
            LEFT JOIN event_types et ON et.id = e.event_type_id
            LEFT JOIN properties p ON p.id = e.property_id
            LEFT JOIN crm_leads l ON l.id = e.lead_id
            LEFT JOIN property_owners po ON po.id = e.contact_id

            LEFT JOIN users cu ON cu.id = TRY_CONVERT(INT, e.assigned_agent_id)

            ORDER BY e.id
        """
        if limit:
            sql += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        with connections["legacy"].cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        self.stdout.write(f"Legacy events: {len(rows)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        status_map = {
            "PENDING": "pending",
            "ACCEPTED": "accepted",
            "REJECTED": "rejected",
        }

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for (
                legacy_id,
                code,
                event_type_name,
                assigned_agent_username,
                assigned_agent_fullname,
                property_code,
                lead_phone,
                contact_fullname,
                interesado_fallback,
                titulo,
                detalle,
                seguimiento,
                fecha_evento,
                hora_inicio,
                hora_fin,
                legacy_status,
                is_active,
            ) in rows:

                code = norm(code) or None

                # event_type por NAME
                et_obj = None
                et_name = norm(event_type_name)
                if et_name:
                    et_obj = EventTypeNew.objects.filter(name__iexact=et_name).first()

                # Si tu modelo new NO permite null aquí, mejor skip (para no reventar)
                if not et_obj:
                    self.stdout.write(self.style.WARNING(f"[SKIP] legacy_id={legacy_id} sin event_type resolvible ({et_name})"))
                    skipped += 1
                    continue

                # ✅ assigned_agent: primero fullname por join CustomUser, sino raw como string
                assigned_agent = None
                un = norm(assigned_agent_username)
                if un:
                    assigned_agent = User.objects.filter(username__iexact=un).first()
                if not assigned_agent:
                    assigned_agent = resolve_user_by_fullname(User, norm(assigned_agent_fullname))

                # lead por phone
                lead_obj = None
                lp = normalize_phone(lead_phone)
                if lp:
                    lead_obj = LeadNew.objects.filter(phone=lp).first() or LeadNew.objects.filter(phone__icontains=lp).first()

                # property por code
                prop_obj = None
                pc = norm(property_code)
                if pc:
                    prop_obj = PropertyNew.objects.filter(code=pc).first()

                # contact por fullname (po fullname -> interesado fallback)
                contact_obj = resolve_contact_by_fullname(ContactNew, contact_fullname) or resolve_contact_by_fullname(ContactNew, interesado_fallback)

                start_dt = combine_date_time(fecha_evento, hora_inicio)
                end_dt = combine_date_time(fecha_evento, hora_fin)

                if not start_dt:
                    self.stdout.write(self.style.WARNING(f"[SKIP] legacy_id={legacy_id} sin start_time válido"))
                    skipped += 1
                    continue

                status = status_map.get((legacy_status or "").strip().upper(), "pending")

                defaults = {
                    "event_type": et_obj,
                    "assigned_agent": assigned_agent,

                    "lead": lead_obj,
                    "match": None,
                    "property": prop_obj,
                    "proposal": None,
                    "contact": contact_obj,

                    "title": titulo or "",
                    "description": (detalle or "").strip() or None,
                    "tracing": (seguimiento or "").strip() or None,

                    "start_time": start_dt,
                    "end_time": end_dt,

                    "status": status,
                    "is_active": bool(is_active),
                }

                _, was_created = EventNew.objects.update_or_create(
                    code=code,
                    defaults=defaults,
                )
                created += 1 if was_created else 0
                updated += 0 if was_created else 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Migración events OK | created={created} updated={updated} skipped={skipped}"
        ))