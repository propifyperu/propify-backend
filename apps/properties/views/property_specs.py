from rest_framework import mixins, viewsets, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from apps.properties.models import Property
from apps.properties.serializers import PropertySpecsSerializer
from apps.properties.serializers.property import PropertyWithSpecsSerializer


class PropertySpecsViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Property.objects.select_related("specs")
    serializer_class = PropertyWithSpecsSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Listar propiedades con especificaciones")
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(specs__isnull=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(PropertyWithSpecsSerializer(page, many=True).data)
        return Response(PropertyWithSpecsSerializer(qs, many=True).data)

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Obtener propiedad con especificaciones por property_id")
    def retrieve(self, request, *args, **kwargs):
        prop = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        return Response(PropertyWithSpecsSerializer(prop).data)

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Crear especificaciones de propiedad")
    def create(self, request, *args, **kwargs):
        prop = get_object_or_404(Property, pk=request.data.get("property"))
        if hasattr(prop, "specs"):
            raise ValidationError({"property": "Esta propiedad ya tiene especificaciones."})
        serializer = PropertySpecsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Actualizar especificaciones de propiedad por property_id")
    def partial_update(self, request, *args, **kwargs):
        prop = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        if not hasattr(prop, "specs"):
            raise NotFound("Esta propiedad no tiene especificaciones.")
        serializer = PropertySpecsSerializer(prop.specs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
