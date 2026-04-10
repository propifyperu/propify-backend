from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.locations.filters import (
    CountryFilter,
    DepartmentFilter,
    ProvinceFilter,
    DistrictFilter,
    UrbanizationFilter,
)

from apps.locations.models import Country, Department, District, Province, Urbanization
from apps.locations.serializers import (
    CountrySerializer,
    DepartmentSerializer,
    DistrictSerializer,
    ProvinceSerializer,
    UrbanizationSerializer,
)

_TAGS = ["Locations"]


class _ReadOnlyViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = None

_COUNTRY_FILTER_PARAMS = []

class CountryViewSet(_ReadOnlyViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar países", manual_parameters=_COUNTRY_FILTER_PARAMS)
    def list(self, request, *args, **kwargs):
        self.queryset = CountryFilter(
            request.query_params, queryset=self.get_queryset(), request=request
        ).qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener país")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

_DEPARTMENT_FILTER_PARAMS = [
    openapi.Parameter("country", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID del país"),
]
class DepartmentViewSet(_ReadOnlyViewSet):
    queryset = Department.objects.select_related("country").all()
    serializer_class = DepartmentSerializer

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar departamentos", manual_parameters=_DEPARTMENT_FILTER_PARAMS)
    def list(self, request, *args, **kwargs):
        self.queryset = DepartmentFilter(
            request.query_params, queryset=self.get_queryset(), request=request
        ).qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener departamento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

_PROVINCE_FILTER_PARAMS = [
    openapi.Parameter("country", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID del país"),
    openapi.Parameter("department", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID del departamento"),
]

class ProvinceViewSet(_ReadOnlyViewSet):
    queryset = Province.objects.select_related("department").all()
    serializer_class = ProvinceSerializer

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar provincias", manual_parameters=_PROVINCE_FILTER_PARAMS)
    def list(self, request, *args, **kwargs):
        self.queryset = ProvinceFilter(
            request.query_params, queryset=self.get_queryset(), request=request
        ).qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener provincia")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

_DISTRICT_FILTER_PARAMS = [
    openapi.Parameter("country",    openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID del país"),
    openapi.Parameter("department", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID del departamento"),
    openapi.Parameter("province",   openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID de la provincia"),
]


class DistrictViewSet(_ReadOnlyViewSet):
    queryset = District.objects.select_related("province__department__country").all()
    serializer_class = DistrictSerializer

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar distritos", manual_parameters=_DISTRICT_FILTER_PARAMS)
    def list(self, request, *args, **kwargs):
        self.queryset = DistrictFilter(
            request.query_params, queryset=self.get_queryset(), request=request
        ).qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener distrito")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

_URBANIZATION_FILTER_PARAMS = [
    openapi.Parameter("country", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID del país"),
    openapi.Parameter("department", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID del departamento"),
    openapi.Parameter("province", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID de la provincia"),
    openapi.Parameter("district", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="ID del distrito"),
]

class UrbanizationViewSet(_ReadOnlyViewSet):
    queryset = Urbanization.objects.select_related("district__province__department__country").all()
    serializer_class = UrbanizationSerializer

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar urbanizaciones", manual_parameters=_URBANIZATION_FILTER_PARAMS)
    def list(self, request, *args, **kwargs):
        self.queryset = UrbanizationFilter(
            request.query_params, queryset=self.get_queryset(), request=request
        ).qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener urbanización")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)