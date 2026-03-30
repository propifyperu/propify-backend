import django_filters
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.properties.geo import get_bounding_box
from apps.properties.models import Property


class _CommaSeparatedIDFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    """Acepta un único ID o varios separados por coma: ?property_type=1  o  ?property_type=1,2,3"""
    pass


class PropertyCardFilter(django_filters.FilterSet):
    # --- Catálogos (single o multi-valor separado por coma) ---
    property_type      = _CommaSeparatedIDFilter(field_name="property_type_id")
    property_subtype   = _CommaSeparatedIDFilter(field_name="property_subtype_id")
    property_condition = _CommaSeparatedIDFilter(field_name="property_condition_id")
    operation_type     = _CommaSeparatedIDFilter(field_name="operation_type_id")
    currency           = _CommaSeparatedIDFilter(field_name="currency_id")
    property_status    = _CommaSeparatedIDFilter(field_name="property_status_id")
    district           = _CommaSeparatedIDFilter(field_name="district_id")
    urbanization       = _CommaSeparatedIDFilter(field_name="urbanization_id")
    responsible        = _CommaSeparatedIDFilter(field_name="responsible_id")

    # --- Búsqueda simple ---
    search = django_filters.CharFilter(method="filter_search")

    # --- Precio ---
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    # --- Specs ---
    bedrooms_min  = django_filters.NumberFilter(field_name="specs__bedrooms",   lookup_expr="gte")
    bathrooms_min = django_filters.NumberFilter(field_name="specs__bathrooms",  lookup_expr="gte")
    land_area_min = django_filters.NumberFilter(field_name="specs__land_area",  lookup_expr="gte")
    land_area_max = django_filters.NumberFilter(field_name="specs__land_area",  lookup_expr="lte")
    built_area_min = django_filters.NumberFilter(field_name="specs__built_area", lookup_expr="gte")
    built_area_max = django_filters.NumberFilter(field_name="specs__built_area", lookup_expr="lte")

    # --- Fecha de creación ---
    created_last_days = django_filters.NumberFilter(method="filter_created_last_days")

    # --- Ubicación (bounding box) ---
    latitude  = django_filters.NumberFilter(method="filter_by_location")
    longitude = django_filters.NumberFilter(method="filter_by_location")
    radius_m  = django_filters.NumberFilter(method="filter_by_location")

    class Meta:
        model = Property
        fields = []

    def filter_created_last_days(self, queryset, name, value):
        try:
            days = int(value)
        except (TypeError, ValueError):
            return queryset
        if days <= 0:
            return queryset
        since = timezone.now() - timedelta(days=days)
        return queryset.filter(created_at__gte=since)

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(code__icontains=value)
            | Q(title__icontains=value)
            | Q(map_address__icontains=value)
            | Q(display_address__icontains=value)
        )

    def filter_by_location(self, queryset, name, value):
        # Se aplica solo cuando los 3 params están presentes; se dispara una vez por param
        # pero solo actúa en la última llamada cuando ya todos están disponibles.
        try:
            lat  = float(self.data.get("latitude",  ""))
            lon  = float(self.data.get("longitude", ""))
            rad  = float(self.data.get("radius_m",  ""))
        except (TypeError, ValueError):
            return queryset

        # Solo actuar cuando se procesa el último de los tres params para no filtrar 3 veces
        if name != "radius_m":
            return queryset

        bbox = get_bounding_box(lat, lon, rad)
        return queryset.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            latitude__gte=bbox["lat_min"],
            latitude__lte=bbox["lat_max"],
            longitude__gte=bbox["lon_min"],
            longitude__lte=bbox["lon_max"],
        )
