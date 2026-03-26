import django_filters
from django.db.models import Q

from apps.users.models import User


class _CommaSeparatedIDFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    """Acepta un único ID o varios separados por coma: ?role=1  o  ?role=1,2,3"""
    pass


class UserFilter(django_filters.FilterSet):
    role      = _CommaSeparatedIDFilter(field_name="role_id")
    is_active = django_filters.BooleanFilter(field_name="is_active")
    search    = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = User
        fields = []

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(username__icontains=value)
            | Q(email__icontains=value)
        )
