from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """
    Admin base para modelos que heredan de BaseModel (name + is_active + audit).
    Reutilizable en cualquier dominio.
    """
    list_display = ("id", "name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
