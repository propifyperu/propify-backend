import django_filters
from datetime import timedelta

from apps.crm.models import Event


class _CommaSeparatedIDFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    """Acepta un único ID o varios separados por coma: ?event_type=1  o  ?event_type=1,2,3"""
    pass


class EventFilter(django_filters.FilterSet):
    assigned_agent = _CommaSeparatedIDFilter(field_name="assigned_agent_id")
    event_type     = _CommaSeparatedIDFilter(field_name="event_type_id")
    property       = _CommaSeparatedIDFilter(field_name="property_id")
    status         = django_filters.CharFilter(field_name="status")

    # date params (usados por el método custom)
    date_mode  = django_filters.CharFilter(method="filter_by_date")
    date       = django_filters.CharFilter(method="filter_by_date")
    date_from  = django_filters.CharFilter(method="filter_by_date")
    date_to    = django_filters.CharFilter(method="filter_by_date")

    class Meta:
        model = Event
        fields = []

    def filter_by_date(self, queryset, name, value):
        # Se ejecuta una vez por param; solo actuamos cuando procesamos date_mode
        if name != "date_mode":
            return queryset

        mode      = self.data.get("date_mode", "")
        date_str  = self.data.get("date", "")
        date_from = self.data.get("date_from", "")
        date_to   = self.data.get("date_to", "")

        try:
            from datetime import date as date_cls
            if mode == "day":
                d = date_cls.fromisoformat(date_str)
                return queryset.filter(start_time__date=d)

            if mode == "week":
                d = date_cls.fromisoformat(date_str)
                week_start = d - timedelta(days=d.weekday())
                week_end   = week_start + timedelta(days=6)
                return queryset.filter(start_time__date__gte=week_start, start_time__date__lte=week_end)

            if mode == "month":
                d = date_cls.fromisoformat(date_str)
                return queryset.filter(start_time__year=d.year, start_time__month=d.month)

            if mode == "range":
                d_from = date_cls.fromisoformat(date_from)
                d_to   = date_cls.fromisoformat(date_to)
                return queryset.filter(start_time__date__gte=d_from, start_time__date__lte=d_to)

        except (ValueError, TypeError):
            pass

        return queryset
