from django.contrib import admin

from .models import (
    Contact,
    Event,
    ExchangeRate,
    Lead,
    Match,
    Proposal,
    Requirement,
    RequirementMatch,
)


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "contact_type", "phone", "email", "is_active", "assigned_agent", "created_at")
    list_filter = ("is_active", "contact_type", "document_type", "gender")
    search_fields = ("full_name", "phone", "email", "document_number")
    autocomplete_fields = ("assigned_agent",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


# ---------------------------------------------------------------------------
# Lead
# ---------------------------------------------------------------------------

class RequirementInline(admin.TabularInline):
    model = Requirement
    extra = 0
    fields = ("operation_type", "property_type", "price_min", "price_max", "currency", "is_active")
    show_change_link = True


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "id", "full_name", "phone", "lead_status", "canal_lead",
        "assigned_to", "is_active", "date_entry", "created_at",
    )
    list_filter = ("is_active", "lead_status", "canal_lead", "area")
    search_fields = ("full_name", "phone", "email", "id_chatwoot")
    autocomplete_fields = ("contact", "assigned_to", "area", "lead_status", "canal_lead")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    filter_horizontal = ("operation_types", "properties")
    date_hierarchy = "created_at"
    inlines = [RequirementInline]


# ---------------------------------------------------------------------------
# Requirement
# ---------------------------------------------------------------------------

@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = (
        "id", "lead", "operation_type", "property_type",
        "price_min", "price_max", "currency", "is_active", "created_at",
    )
    list_filter = ("is_active", "operation_type", "property_type", "currency")
    search_fields = ("lead__full_name", "import_batch")
    autocomplete_fields = (
        "lead", "assigned_to", "operation_type", "property_type",
        "property_subtype", "property_condition", "currency", "payment_method",
    )
    filter_horizontal = ("districts", "urbanizations")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


# ---------------------------------------------------------------------------
# RequirementMatch
# ---------------------------------------------------------------------------

@admin.register(RequirementMatch)
class RequirementMatchAdmin(admin.ModelAdmin):
    list_display = ("id", "requirement", "property", "score", "is_active", "computed_at")
    list_filter = ("is_active",)
    search_fields = ("requirement__id", "property__title")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "computed_at", "details")


# ---------------------------------------------------------------------------
# Match
# ---------------------------------------------------------------------------

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("id", "property", "lead", "match_status", "requested_by_user", "created_at")
    list_filter = ("match_status",)
    search_fields = ("property__title", "lead__full_name")
    autocomplete_fields = ("property", "lead", "requirement", "requirementmatch", "requested_by_user")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


# ---------------------------------------------------------------------------
# Proposal
# ---------------------------------------------------------------------------

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = (
        "id", "property", "lead", "amount", "currency",
        "status", "requested_by_user", "responded_at", "created_at",
    )
    list_filter = ("status", "currency", "payment_method")
    search_fields = ("property__title", "lead__full_name")
    autocomplete_fields = (
        "property", "lead", "requirement_match",
        "currency", "payment_method",
        "requested_by_user", "responded_by_user",
    )
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "responded_at")


# ---------------------------------------------------------------------------
# ExchangeRate
# ---------------------------------------------------------------------------

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("id", "base_currency", "quote_currency", "rate", "rate_date", "provider", "is_active")
    list_filter = ("is_active", "base_currency", "quote_currency")
    search_fields = ("provider",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    date_hierarchy = "rate_date"


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id", "code", "title", "event_type", "assigned_agent",
        "status", "start_time", "end_time", "is_active",
    )
    list_filter = ("status", "is_active", "event_type")
    search_fields = ("code", "title", "description")
    autocomplete_fields = (
        "event_type", "assigned_agent",
        "lead", "match", "property", "proposal", "contact",
    )
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    date_hierarchy = "start_time"
