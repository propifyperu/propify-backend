from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.properties.models import Property
from apps.properties.serializers import PropertySerializer
from apps.properties.serializers.property import (
    PropertyCardSerializer,
    PropertyCreateFullSerializer,
    PropertyFullDetailSerializer,
)


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

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Listado de tarjetas de propiedades",
        operation_description="Devuelve propiedades con los campos necesarios para las tarjetas del listado.",
    )
    @action(detail=False, methods=["get"])
    def cards(self, request):
        qs = (
            Property.objects
            .select_related(
                "property_type", "property_subtype", "property_condition",
                "operation_type", "currency", "property_status", "responsible",
                "specs",
            )
            .prefetch_related("media")
        )
        serializer = PropertyCardSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Detalle completo de propiedad",
        operation_description="Retorna la propiedad con todos sus sub-objetos anidados: specs, financial, media y documents.",
    )
    @action(detail=True, methods=["get"], url_path="full-detail")
    def full_detail(self, request, pk=None):
        instance = self.get_object()
        serializer = PropertyFullDetailSerializer(instance, context={"request": request})
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Crear propiedad completa",
        operation_description=(
            "Crea una propiedad junto con todos sus sub-objetos en una sola transacción atómica. "
            "Payload esperado: { property, specs?, financial_info?, media[]?, documents[]? }"
        ),
    )
    @action(detail=False, methods=["post"], url_path="create-full")
    def create_full(self, request):
        serializer = PropertyCreateFullSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        prop = serializer.save()
        # Recargar con todas las relaciones para devolver el detalle completo
        prop.refresh_from_db()
        output = PropertyFullDetailSerializer(prop, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)
