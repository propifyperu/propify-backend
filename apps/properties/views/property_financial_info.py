from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.properties.models import Property, PropertyFinancialInfo
from apps.properties.serializers.property_financial_info import (
    PropertyFinancialInfoSerializer,
    PropertyWithFinancialSerializer,
)


class PropertyFinancialInfoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Property.objects.select_related(
        "property_type", "property_subtype", "operation_type",
        "currency", "property_status", "financial",
    ).filter(financial__isnull=False)
    serializer_class = PropertyWithFinancialSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Listar propiedades con información financiera",
        operation_description="Devuelve las propiedades que tienen información financiera registrada, con un resumen de la propiedad y el objeto financiero anidado.",
    )
    def list(self, request, *args, **kwargs):
        serializer = PropertyWithFinancialSerializer(self.get_queryset(), many=True, context={"request": request})
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Obtener propiedad con información financiera por property_id",
        operation_description="El `{id}` de la URL corresponde al `property_id`. Devuelve la propiedad con su información financiera anidada.",
    )
    def retrieve(self, request, *args, **kwargs):
        prop = self._get_property(kwargs["pk"])
        serializer = PropertyWithFinancialSerializer(prop, context={"request": request})
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Crear información financiera de propiedad",
        operation_description=(
            "Crea la información financiera para una propiedad. "
            "El body debe incluir `property` (id de la propiedad) más los campos financieros. "
            "Retorna 400 si la propiedad ya tiene información financiera registrada."
        ),
    )
    def create(self, request, *args, **kwargs):
        property_id = request.data.get("property")
        if not property_id:
            return Response({"detail": "El campo 'property' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            prop = Property.objects.get(pk=property_id)
        except Property.DoesNotExist:
            return Response({"detail": "Propiedad no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(prop, "financial"):
            return Response({"detail": "Esta propiedad ya tiene información financiera."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PropertyFinancialInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Actualizar información financiera de propiedad por property_id",
        operation_description=(
            "El `{id}` de la URL corresponde al `property_id`. "
            "Aplica una actualización parcial sobre la información financiera de esa propiedad. "
            "Retorna 404 si la propiedad no tiene información financiera registrada."
        ),
    )
    def partial_update(self, request, *args, **kwargs):
        prop = self._get_property(kwargs["pk"])
        try:
            financial = prop.financial
        except PropertyFinancialInfo.DoesNotExist:
            return Response({"detail": "Esta propiedad no tiene información financiera."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PropertyFinancialInfoSerializer(financial, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ---------------------------------------------------------------------------
    # Helper
    # ---------------------------------------------------------------------------

    def _get_property(self, pk):
        try:
            return Property.objects.select_related(
                "property_type", "property_subtype", "operation_type",
                "currency", "property_status", "financial",
            ).get(pk=pk)
        except Property.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Propiedad no encontrada.")
