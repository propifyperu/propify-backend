import django_filters

from apps.locations.models import District


class DistrictFilter(django_filters.FilterSet):
    country    = django_filters.NumberFilter(field_name="province__department__country_id")
    department = django_filters.NumberFilter(field_name="province__department_id")
    province   = django_filters.NumberFilter(field_name="province_id")

    class Meta:
        model = District
        fields = []
