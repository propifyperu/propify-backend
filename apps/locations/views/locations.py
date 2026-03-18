from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

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


class CountryViewSet(_ReadOnlyViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar países")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener país")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class DepartmentViewSet(_ReadOnlyViewSet):
    queryset = Department.objects.select_related("country").all()
    serializer_class = DepartmentSerializer

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar departamentos")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener departamento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class ProvinceViewSet(_ReadOnlyViewSet):
    queryset = Province.objects.select_related("department").all()
    serializer_class = ProvinceSerializer

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar provincias")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener provincia")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class DistrictViewSet(_ReadOnlyViewSet):
    queryset = District.objects.select_related("province").all()
    serializer_class = DistrictSerializer

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar distritos")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener distrito")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class UrbanizationViewSet(_ReadOnlyViewSet):
    queryset = Urbanization.objects.select_related("district").all()
    serializer_class = UrbanizationSerializer

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar urbanizaciones")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener urbanización")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
