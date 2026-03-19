from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connections, transaction

from apps.users.models import Area, Role, UserProfile
from apps.locations.models import Country

User = get_user_model()


class Command(BaseCommand):
    help = "Migra usuarios desde legacy (Azure SQL) hacia la DB nueva."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo simula.")
        parser.add_argument("--peru-code", default="PER")
        parser.add_argument("--peru-name", default="Perú")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        peru_code = options["peru_code"]
        peru_name = options["peru_name"]

        self.stdout.write(self.style.MIGRATE_HEADING("== Migración users (legacy → new) =="))

        # 1) Asegurar Country Perú (si ya existe por locations, solo lo usamos)
        if dry_run:
            peru = Country(code=peru_code, name=peru_name, is_active=True)
        else:
            peru, _ = Country.objects.update_or_create(
                code=peru_code,
                defaults={"name": peru_name, "is_active": True},
            )

        area_map = {}
        role_map = {}
        user_map = {}

        with connections["legacy"].cursor() as cursor:
            # Areas
            cursor.execute("SELECT id, name, is_active FROM departments")
            legacy_areas = cursor.fetchall()
            self.stdout.write(f"Areas legacy: {len(legacy_areas)}")

            # Roles
            cursor.execute("SELECT id, area_id, name, is_active FROM roles")
            legacy_roles = cursor.fetchall()
            self.stdout.write(f"Roles legacy: {len(legacy_roles)}")

            # Users
            cursor.execute("""
                SELECT
                    id, username, first_name, last_name, email,
                    password, last_login, is_superuser, is_staff, is_active, date_joined,
                    role_id, area_id, phone, is_verified
                FROM users
            """)
            legacy_users = cursor.fetchall()
            self.stdout.write(f"Users legacy: {len(legacy_users)}")

            # Profiles
            cursor.execute("""
                SELECT
                    id, user_id, avatar, address, date_of_birth
                FROM user_profiles
            """)
            legacy_profiles = cursor.fetchall()
            self.stdout.write(f"UserProfiles legacy: {len(legacy_profiles)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN activado: no se escribirá nada."))
            return

        with transaction.atomic():
            # 2) Migrar Areas (unique: name)
            for legacy_id, name, is_active in legacy_areas:
                if not name:
                    continue
                obj, _ = Area.objects.update_or_create(
                    name=str(name).strip(),
                    defaults={"is_active": bool(is_active)},
                )
                area_map[int(legacy_id)] = obj

            # 3) Migrar Roles (unique: name)
            for legacy_id, area_id, name, is_active in legacy_roles:
                if not name:
                    continue

                area_obj = area_map.get(int(area_id)) if area_id is not None else None
                if not area_obj:
                    # En tu data parece que siempre hay area, pero por si acaso:
                    self.stdout.write(self.style.WARNING(f"Role {legacy_id} sin area {area_id}, skip"))
                    continue

                obj, _ = Role.objects.update_or_create(
                    name=str(name).strip(),
                    defaults={
                        "area": area_obj,
                        "is_active": bool(is_active),
                    },
                )
                role_map[int(legacy_id)] = obj

            # Helper: detectar si password parece hash Django
            def _looks_like_django_hash(pw: str) -> bool:
                if not pw:
                    return False
                return "$" in pw and (pw.startswith("pbkdf2_") or pw.startswith("argon2$") or pw.startswith("bcrypt$"))

            # 4) Migrar Users
            for (
                legacy_id, username, first_name, last_name, email,
                password, last_login, is_superuser, is_staff, is_active, date_joined,
                role_id, area_id, phone, is_verified
            ) in legacy_users:

                legacy_id = int(legacy_id)

                # 4.1) Resolver Role
                role_obj = role_map.get(int(role_id)) if role_id is not None else None

                # 4.2) Upsert por external_id (si ya migramos antes)
                external_id = str(legacy_id)

                user = User.objects.filter(external_id=external_id).first()

                # Si no existe por external_id, intentamos por email o username para “enganchar” usuarios existentes
                if not user and email:
                    user = User.objects.filter(email__iexact=str(email).strip()).first()
                if not user and username:
                    user = User.objects.filter(username=str(username).strip()).first()

                creating = user is None
                if creating:
                    user = User(external_id=external_id)

                # Campos base
                user.username = (str(username).strip() if username else f"user_{legacy_id}")
                user.first_name = str(first_name or "").strip()
                user.last_name = str(last_name or "").strip()
                user.email = (str(email).strip() if email else "")
                user.is_superuser = bool(is_superuser)
                user.is_staff = bool(is_staff)
                user.is_active = bool(is_active)
                user.last_login = last_login
                user.date_joined = date_joined
                user.role = role_obj
                user.email_verified = bool(is_verified)
                user.phone_verified = False  # no hay equivalente claro en legacy

                # Password: hash vs raw
                pw = str(password or "")
                if _looks_like_django_hash(pw):
                    user.password = pw
                elif pw:
                    # Caso texto plano tipo "12345"
                    user.set_password(pw)
                else:
                    user.set_unusable_password()

                user.save()
                user_map[legacy_id] = user

                # 4.3) Asegurar UserProfile SIEMPRE (esto resuelve tu problema de PATCH 404)
                UserProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        "phone": (str(phone).strip() if phone else None),
                        "country": peru,
                    },
                )

            # 5) Migrar UserProfile (complementar data)
            for legacy_prof_id, legacy_user_id, avatar, address, date_of_birth in legacy_profiles:
                legacy_user_id = int(legacy_user_id)
                user = user_map.get(legacy_user_id)
                if not user:
                    self.stdout.write(self.style.WARNING(f"Profile {legacy_prof_id} sin user {legacy_user_id}, skip"))
                    continue

                profile, _ = UserProfile.objects.get_or_create(user=user)

                # avatar: solo asignamos el PATH del blob ya existente (NO subimos)
                if avatar:
                    profile.avatar_url.name = str(avatar).strip()

                if address:
                    profile.address = str(address).strip()

                profile.birth_date = date_of_birth
                # phone ya se seteo arriba; aquí no lo tocamos
                # city no existe en legacy -> queda None

                profile.save()

        self.stdout.write(self.style.SUCCESS("✅ Migración users terminada OK"))