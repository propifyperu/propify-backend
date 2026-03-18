from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from apps.properties.models import Property
from apps.properties.serializers import PropertySerializer


class PropertyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Property.objects.select_related(
        "contact",
        "property_type",
        "property_subtype",
        "property_condition",
        "operation_type",
        "currency",
        "payment_method",
        "district",
        "urbanization",
        "property_status",
        "responsible",
    ).all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Listar propiedades")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Obtener propiedad")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Crear propiedad")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Actualizar propiedad parcialmente")
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
