import django_filters
from datetime import date as date_cls, timedelta

from django.db.models import Q

from apps.crm.models import Contact, Event, Lead, Requirement


class _CommaSeparatedIDFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    """Acepta un único ID o varios separados por coma: ?event_type=1  o  ?event_type=1,2,3"""
    pass


def _apply_date_mode(queryset, data, date_field):
    """
    Aplica filtro de fecha sobre `date_field` según date_mode.
    Reutilizable por cualquier FilterSet que lo invoque.
    """
    mode      = data.get("date_mode", "")
    date_str  = data.get("date", "")
    date_from = data.get("date_from", "")
    date_to   = data.get("date_to", "")

    try:
        if mode == "day":
            d = date_cls.fromisoformat(date_str)
            return queryset.filter(**{f"{date_field}__date": d})

        if mode == "week":
            d = date_cls.fromisoformat(date_str)
            week_start = d - timedelta(days=d.weekday())
            week_end   = week_start + timedelta(days=6)
            return queryset.filter(**{
                f"{date_field}__date__gte": week_start,
                f"{date_field}__date__lte": week_end,
            })

        if mode == "month":
            d = date_cls.fromisoformat(date_str)
            return queryset.filter(**{f"{date_field}__year": d.year, f"{date_field}__month": d.month})

        if mode == "range":
            d_from = date_cls.fromisoformat(date_from)
            d_to   = date_cls.fromisoformat(date_to)
            return queryset.filter(**{
                f"{date_field}__date__gte": d_from,
                f"{date_field}__date__lte": d_to,
            })

    except (ValueError, TypeError):
        pass

    return queryset


class ContactFilter(django_filters.FilterSet):
    full_name     = django_filters.CharFilter(method="filter_full_name")
    email         = django_filters.CharFilter(field_name="email",         lookup_expr="icontains")
    phone         = django_filters.CharFilter(field_name="phone",         lookup_expr="icontains")
    document_type = django_filters.CharFilter(field_name="document_type", lookup_expr="exact")
    ordering = django_filters.CharFilter(method="filter_ordering")

    class Meta:
        model = Contact
        fields = []

    def filter_full_name(self, queryset, name, value):
        terms = value.split()
        q = Q()
        for term in terms:
            q &= Q(first_name__icontains=term) | Q(last_name__icontains=term)
        return queryset.filter(q)
    
    def filter_ordering(self, queryset, name, value):
        if value == "created_at":
            return queryset.order_by("created_at")

        if value == "-created_at":
            return queryset.order_by("-created_at")

        if value == "full_name":
            return queryset.order_by("first_name", "last_name")

        if value == "-full_name":
            return queryset.order_by("-first_name", "-last_name")

        return queryset


class EventFilter(django_filters.FilterSet):
    assigned_agent = _CommaSeparatedIDFilter(field_name="assigned_agent_id")
    event_type     = _CommaSeparatedIDFilter(field_name="event_type_id")
    property       = _CommaSeparatedIDFilter(field_name="property_id")
    status         = django_filters.CharFilter(field_name="status")

    date_mode  = django_filters.CharFilter(method="filter_by_date")
    date       = django_filters.CharFilter(method="filter_by_date")
    date_from  = django_filters.CharFilter(method="filter_by_date")
    date_to    = django_filters.CharFilter(method="filter_by_date")

    class Meta:
        model = Event
        fields = []

    def filter_by_date(self, queryset, name, value):
        if name != "date_mode":
            return queryset
        return _apply_date_mode(queryset, self.data, "start_time")


class RequirementFilter(django_filters.FilterSet):
    assigned_to        = _CommaSeparatedIDFilter(field_name="assigned_to_id")
    lead               = _CommaSeparatedIDFilter(field_name="lead_id")
    operation_type     = _CommaSeparatedIDFilter(field_name="operation_type_id")
    property_type      = _CommaSeparatedIDFilter(field_name="property_type_id")
    property_subtype   = _CommaSeparatedIDFilter(field_name="property_subtype_id")
    property_condition = _CommaSeparatedIDFilter(field_name="property_condition_id")
    currency           = _CommaSeparatedIDFilter(field_name="currency_id")
    payment_method     = _CommaSeparatedIDFilter(field_name="payment_method_id")

    districts     = django_filters.CharFilter(method="filter_districts")
    urbanizations = django_filters.CharFilter(method="filter_urbanizations")

    has_elevator       = django_filters.BooleanFilter(field_name="has_elevator")
    pet_friendly       = django_filters.BooleanFilter(field_name="pet_friendly")
    ordering           = django_filters.OrderingFilter(fields=["created_at"])

    date_mode  = django_filters.CharFilter(method="filter_by_date")
    date       = django_filters.CharFilter(method="filter_by_date")
    date_from  = django_filters.CharFilter(method="filter_by_date")
    date_to    = django_filters.CharFilter(method="filter_by_date")

    class Meta:
        model = Requirement
        fields = []

    def filter_districts(self, queryset, name, value):
        values = [v.strip() for v in str(value).split(",") if v.strip()]
        if not values:
            return queryset
        return queryset.filter(districts__id__in=values).distinct()

    def filter_urbanizations(self, queryset, name, value):
        values = [v.strip() for v in str(value).split(",") if v.strip()]
        if not values:
            return queryset
        return queryset.filter(urbanizations__id__in=values).distinct()

    def filter_by_date(self, queryset, name, value):
        if name != "date_mode":
            return queryset
        return _apply_date_mode(queryset, self.data, "created_at")


class LeadFilter(django_filters.FilterSet):
    assigned_to  = _CommaSeparatedIDFilter(field_name="assigned_to_id")
    lead_status  = _CommaSeparatedIDFilter(field_name="lead_status_id")
    canal_lead   = _CommaSeparatedIDFilter(field_name="canal_lead_id")

    full_name = django_filters.CharFilter(field_name="full_name", lookup_expr="icontains")
    phone     = django_filters.CharFilter(field_name="phone",     lookup_expr="icontains")
    username  = django_filters.CharFilter(field_name="username",  lookup_expr="icontains")

    operation_types = django_filters.CharFilter(method="filter_operation_types")
    properties      = django_filters.CharFilter(method="filter_properties")

    ordering = django_filters.OrderingFilter(
        fields=["date_entry", "full_name"],
    )

    date_mode  = django_filters.CharFilter(method="filter_by_date")
    date       = django_filters.CharFilter(method="filter_by_date")
    date_from  = django_filters.CharFilter(method="filter_by_date")
    date_to    = django_filters.CharFilter(method="filter_by_date")

    class Meta:
        model = Lead
        fields = []

    def filter_operation_types(self, queryset, name, value):
        ids = [v.strip() for v in str(value).split(",") if v.strip()]
        if not ids:
            return queryset
        return queryset.filter(operation_types__id__in=ids).distinct()

    def filter_properties(self, queryset, name, value):
        ids = [v.strip() for v in str(value).split(",") if v.strip()]
        if not ids:
            return queryset
        return queryset.filter(properties__id__in=ids).distinct()

    def filter_by_date(self, queryset, name, value):
        if name != "date_mode":
            return queryset
        return _apply_date_mode(queryset, self.data, "date_entry")