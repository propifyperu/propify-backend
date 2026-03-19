from django.contrib import admin

from common.admin import BaseModelAdmin

from .models import (
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


# ---------------------------------------------------------------------------
# PropertyType + inline PropertySubtype
# ---------------------------------------------------------------------------

class PropertySubtypeInline(admin.TabularInline):
    model = PropertySubtype
    extra = 0
    fields = ("name", "is_active")


@admin.register(PropertyType)
class PropertyTypeAdmin(BaseModelAdmin):
    inlines = [PropertySubtypeInline]


@admin.register(PropertySubtype)
class PropertySubtypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "property_type", "is_active", "created_at")
    list_filter = ("is_active", "property_type")
    search_fields = ("name", "property_type__name")
    autocomplete_fields = ("property_type",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


# ---------------------------------------------------------------------------
# Simple BaseModel catalogs
# ---------------------------------------------------------------------------

@admin.register(PropertyStatus)
class PropertyStatusAdmin(BaseModelAdmin):
    pass


@admin.register(PropertyCondition)
class PropertyConditionAdmin(BaseModelAdmin):
    pass


@admin.register(OperationType)
class OperationTypeAdmin(BaseModelAdmin):
    pass


@admin.register(PaymentMethod)
class PaymentMethodAdmin(BaseModelAdmin):
    pass


@admin.register(CanalLead)
class CanalLeadAdmin(BaseModelAdmin):
    pass


@admin.register(LeadStatus)
class LeadStatusAdmin(BaseModelAdmin):
    pass


@admin.register(EventType)
class EventTypeAdmin(BaseModelAdmin):
    pass


# ---------------------------------------------------------------------------
# Richer catalogs
# ---------------------------------------------------------------------------

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "symbol", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


@admin.register(UtilityService)
class UtilityServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "name", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("category", "name")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
