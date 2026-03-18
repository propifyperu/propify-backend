from rest_framework import serializers
from apps.locations.models import Country, Department, Province, District, Urbanization


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "code", "is_active"]


class DepartmentSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Department
        fields = ["id", "country", "country_name", "name", "is_active"]


class ProvinceSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Province
        fields = ["id", "department", "department_name", "name", "is_active"]


class DistrictSerializer(serializers.ModelSerializer):
    province_name = serializers.CharField(source="province.name", read_only=True)

    class Meta:
        model = District
        fields = ["id", "province", "province_name", "name", "is_active"]


class UrbanizationSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source="district.name", read_only=True)

    class Meta:
        model = Urbanization
        fields = ["id", "district", "district_name", "name", "is_active"]
