from django.contrib import admin

from .models import Property, PropertyDocument, PropertyFinancialInfo, PropertyMedia, PropertySpecs


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class PropertySpecsInline(admin.StackedInline):
    model = PropertySpecs
    extra = 0
    can_delete = False
    fields = (
        "bedrooms", "bathrooms", "half_bathrooms",
        "land_area", "built_area", "area_unit","linear_unit","front_measure","depth_measure",
        "floors_total", "unit_location",
        "garage_spaces", "garage_type", "parking_cost_included", "parking_cost",
        "antiquity_years", "delivery_date",
        "has_elevator", "has_security", "has_pool", "has_garden",
        "has_bbq", "has_terrace", "has_air_conditioning",
        "has_laundry_area", "has_service_room", "pet_friendly",
        "water_service", "energy_service", "drainage_service", "gas_service",
    )


class PropertyFinancialInfoInline(admin.StackedInline):
    model = PropertyFinancialInfo
    extra = 0
    can_delete = False
    fields = (
        "contract_type",
        "commission_initial", "commission_final", "commission_pf",
        "negotiation_status", "notes",
    )


class PropertyMediaInline(admin.TabularInline):
    model = PropertyMedia
    extra = 0
    fields = ("media_type", "file", "title", "label", "order")


class PropertyDocumentInline(admin.TabularInline):
    model = PropertyDocument
    extra = 0
    fields = ("document_type", "file", "valid_from", "valid_to", "status")


# ---------------------------------------------------------------------------
# Property
# ---------------------------------------------------------------------------

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "id","code","contact", "title", "property_type","property_subtype","property_condition", "operation_type",
        "property_status", "district","urbanization", "price", "currency","payment_method",
        "responsible", "created_at","wp_post_id","wp_slug","wp_last_sync","is_project","project_name","uuid","maintenance_fee",
        "map_address","display_address","latitude","longitude","registry_number"
    )
    list_filter = (
        "property_type", "operation_type", "property_status",
        "property_condition", "is_project",
    )
    search_fields = ("title", "description", "display_address", "registry_number", "uuid")
    autocomplete_fields = (
        "contact", "property_type", "property_subtype", "property_condition",
        "operation_type", "currency", "payment_method",
        "district", "urbanization", "property_status", "responsible",
    )
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "uuid")
    date_hierarchy = "created_at"

    inlines = [PropertySpecsInline, PropertyFinancialInfoInline, PropertyMediaInline, PropertyDocumentInline]

    fieldsets = (
        ("Identificación", {
            "fields": ("uuid", "title", "description", "is_project", "project_name", "registry_number"),
        }),
        ("Clasificación", {
            "fields": (
                "property_type", "property_subtype", "property_condition",
                "operation_type", "property_status",
            ),
        }),
        ("Precio", {
            "fields": ("price", "currency", "payment_method", "maintenance_fee"),
        }),
        ("Ubicación", {
            "fields": ("district", "urbanization", "map_address", "display_address", "latitude", "longitude"),
        }),
        ("Relaciones", {
            "fields": ("contact", "responsible"),
        }),
        ("WordPress", {
            "fields": ("wp_post_id", "wp_slug", "wp_last_sync"),
            "classes": ("collapse",),
        }),
        ("Auditoría", {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",),
        }),
    )


# ---------------------------------------------------------------------------
# PropertyMedia  (vista independiente)
# ---------------------------------------------------------------------------

@admin.register(PropertyMedia)
class PropertyMediaAdmin(admin.ModelAdmin):
    list_display = ("id", "property", "media_type","file", "title", "order", "created_at")
    list_filter = ("media_type",)
    search_fields = ("property__title", "title")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


# ---------------------------------------------------------------------------
# PropertyDocument  (vista independiente)
# ---------------------------------------------------------------------------

@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "property", "document_type", "status", "valid_from", "valid_to", "created_at")
    list_filter = ("document_type", "status")
    search_fields = ("property__title",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
