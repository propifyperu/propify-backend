from django.contrib import admin

from common.admin import BaseModelAdmin

from .models import Country, Department, District, Province, Urbanization


# ---------------------------------------------------------------------------
# Country  (inline de Departments)
# ---------------------------------------------------------------------------

class DepartmentInline(admin.TabularInline):
    model = Department
    extra = 0
    fields = ("name", "is_active")
    show_change_link = True


@admin.register(Country)
class CountryAdmin(BaseModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    search_fields = ("name", "code")
    inlines = [DepartmentInline]


# ---------------------------------------------------------------------------
# Department  (inline de Provinces)
# ---------------------------------------------------------------------------

class ProvinceInline(admin.TabularInline):
    model = Province
    extra = 0
    fields = ("name", "is_active")
    show_change_link = True


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "is_active", "created_at")
    list_filter = ("is_active", "country")
    search_fields = ("name", "country__name")
    autocomplete_fields = ("country",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    inlines = [ProvinceInline]


# ---------------------------------------------------------------------------
# Province  (inline de Districts)
# ---------------------------------------------------------------------------

class DistrictInline(admin.TabularInline):
    model = District
    extra = 0
    fields = ("name", "is_active")
    show_change_link = True


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "is_active", "created_at")
    list_filter = ("is_active", "department__country")
    search_fields = ("name", "department__name")
    autocomplete_fields = ("department",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    inlines = [DistrictInline]


# ---------------------------------------------------------------------------
# District  (inline de Urbanizations)
# ---------------------------------------------------------------------------

class UrbanizationInline(admin.TabularInline):
    model = Urbanization
    extra = 0
    fields = ("name", "is_active")
    show_change_link = True


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "province", "is_active", "created_at")
    list_filter = ("is_active", "province__department__country")
    search_fields = ("name", "province__name")
    autocomplete_fields = ("province",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    inlines = [UrbanizationInline]


# ---------------------------------------------------------------------------
# Urbanization
# ---------------------------------------------------------------------------

@admin.register(Urbanization)
class UrbanizationAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "district__name")
    autocomplete_fields = ("district",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
