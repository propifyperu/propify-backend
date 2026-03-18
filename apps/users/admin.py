from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from common.admin import BaseModelAdmin

from .models import Area, Role, User, UserProfile


# ---------------------------------------------------------------------------
# Area  (inline de Roles)
# ---------------------------------------------------------------------------

class RoleInline(admin.TabularInline):
    model = Role
    extra = 0
    fields = ("name", "is_active")
    show_change_link = True


@admin.register(Area)
class AreaAdmin(BaseModelAdmin):
    inlines = [RoleInline]


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "area", "is_active", "created_at")
    list_filter = ("is_active", "area")
    search_fields = ("name", "area__name")
    autocomplete_fields = ("area",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


# ---------------------------------------------------------------------------
# UserProfile  (inline de User)
# ---------------------------------------------------------------------------

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fk_name = "user"
    extra = 0
    can_delete = False
    fields = (
        "avatar_url", "birth_date", "nro_document",
        "phone", "address", "country", "city",
    )


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [UserProfileInline]

    list_display = (
        "username", "email", "first_name", "last_name",
        "role", "is_active", "is_staff", "date_joined",
    )
    list_filter = ("is_active", "is_staff", "role__area", "role")
    search_fields = ("username", "first_name", "last_name", "email")
    autocomplete_fields = ("role",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Propify", {"fields": ("role", "external_id", "email_verified", "phone_verified")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Propify", {"fields": ("role",)}),
    )
