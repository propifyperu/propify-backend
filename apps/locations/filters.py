import django_filters

from apps.locations.models import Country, Department, Province, District, Urbanization


class CountryFilter(django_filters.FilterSet):
    class Meta:
        model = Country
        fields = []


class DepartmentFilter(django_filters.FilterSet):
    country = django_filters.NumberFilter(field_name="country_id")

    class Meta:
        model = Department
        fields = []


class ProvinceFilter(django_filters.FilterSet):
    country = django_filters.NumberFilter(field_name="department__country_id")
    department = django_filters.NumberFilter(field_name="department_id")

    class Meta:
        model = Province
        fields = []


class DistrictFilter(django_filters.FilterSet):
    country = django_filters.NumberFilter(field_name="province__department__country_id")
    department = django_filters.NumberFilter(field_name="province__department_id")
    province = django_filters.NumberFilter(field_name="province_id")

    class Meta:
        model = District
        fields = []


class UrbanizationFilter(django_filters.FilterSet):
    country = django_filters.NumberFilter(field_name="district__province__department__country_id")
    department = django_filters.NumberFilter(field_name="district__province__department_id")
    province = django_filters.NumberFilter(field_name="district__province_id")
    district = django_filters.NumberFilter(field_name="district_id")

    class Meta:
        model = Urbanization
        fields = []