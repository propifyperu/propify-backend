from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from apps.catalogs.models import (
    PropertyType,
    PropertySubtype,
    PropertyStatus,
    PropertyCondition,
    OperationType,
    PaymentMethod,
    Currency,
    DocumentType,
    UtilityService,
    CanalLead,
    LeadStatus,
    EventType,
)
from apps.catalogs.serializers import (
    PropertyTypeSerializer,
    PropertySubtypeSerializer,
    PropertyStatusSerializer,
    PropertyConditionSerializer,
    OperationTypeSerializer,
    PaymentMethodSerializer,
    CurrencySerializer,
    DocumentTypeSerializer,
    UtilityServiceSerializer,
    CanalLeadSerializer,
    LeadStatusSerializer,
    EventTypeSerializer,
)


class PropertyTypeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar tipos de propiedad")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener tipo de propiedad")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class PropertySubtypeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PropertySubtype.objects.select_related("property_type").all()
    serializer_class = PropertySubtypeSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar subtipos de propiedad")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener subtipo de propiedad")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class PropertyStatusViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PropertyStatus.objects.all()
    serializer_class = PropertyStatusSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar estados de propiedad")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener estado de propiedad")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class PropertyConditionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PropertyCondition.objects.all()
    serializer_class = PropertyConditionSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar condiciones de propiedad")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener condición de propiedad")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class OperationTypeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = OperationType.objects.all()
    serializer_class = OperationTypeSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar tipos de operación")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener tipo de operación")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class PaymentMethodViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar métodos de pago")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener método de pago")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CurrencyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar monedas")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener moneda")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class DocumentTypeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar tipos de documento")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener tipo de documento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class UtilityServiceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = UtilityService.objects.all()
    serializer_class = UtilityServiceSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar servicios básicos")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener servicio básico")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CanalLeadViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = CanalLead.objects.all()
    serializer_class = CanalLeadSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar canales de lead")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener canal de lead")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class LeadStatusViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = LeadStatus.objects.all()
    serializer_class = LeadStatusSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar estados de lead")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener estado de lead")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class EventTypeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = EventType.objects.all()
    serializer_class = EventTypeSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Listar tipos de evento")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Catálogos"], operation_summary="Obtener tipo de evento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
