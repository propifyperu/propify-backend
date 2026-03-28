import json

from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.properties.models import Property, PropertyMedia
from apps.properties.serializers.property_media import PropertyMediaSerializer, PropertyWithMediaSerializer


class PropertyMediaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Property.objects.prefetch_related("media")
    serializer_class = PropertyWithMediaSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Listar propiedades con medios")
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(media__isnull=False).distinct()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(PropertyWithMediaSerializer(page, many=True).data)
        return Response(PropertyWithMediaSerializer(qs, many=True).data)

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Obtener propiedad con medios por property_id")
    def retrieve(self, request, *args, **kwargs):
        prop = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        return Response(PropertyWithMediaSerializer(prop).data)

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Crear medios para una propiedad",
        operation_description=(
            "Crea múltiples archivos de media para una propiedad en una transacción atómica.\n\n"
            "`media_metadata` es un JSON array alineado por índice con `media_files`."
        ),
        manual_parameters=[
            openapi.Parameter("property", openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=True,
                description="ID de la propiedad"),
            openapi.Parameter("media_files", openapi.IN_FORM, type=openapi.TYPE_FILE, required=True,
                description="Archivos de media (se permiten múltiples)"),
            openapi.Parameter("media_metadata", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True,
                description='JSON array alineado con media_files. Ej: [{"title":"Fachada","label":"principal","order":1,"media_type":"image"}]'),
        ],
        consumes=["multipart/form-data"],
    )
    def create(self, request, *args, **kwargs):
        prop = get_object_or_404(Property, pk=request.data.get("property"))

        try:
            media_metadata = json.loads(request.data.get("media_metadata", "[]") or "[]")
        except json.JSONDecodeError as exc:
            raise ValidationError({"media_metadata": f"JSON inválido: {exc}"})

        media_files = request.FILES.getlist("media_files")

        if len(media_files) != len(media_metadata):
            raise ValidationError({
                "detail": f"media_files tiene {len(media_files)} archivos pero media_metadata tiene {len(media_metadata)} entradas."
            })

        with transaction.atomic():
            created = [
                PropertyMedia.objects.create(
                    property=prop,
                    file=file,
                    media_type=meta.get("media_type", "image"),
                    title=meta.get("title"),
                    label=meta.get("label"),
                    order=meta.get("order", 0),
                )
                for file, meta in zip(media_files, media_metadata)
            ]

        return Response(PropertyMediaSerializer(created, many=True).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Actualizar medios de una propiedad por property_id",
        operation_description=(
            "Actualiza medios de una propiedad en lote dentro de una transacción atómica.\n\n"
            "- `existing_media`: actualiza metadata de media existentes (no reemplaza el archivo).\n"
            "- `media_files` + `media_metadata`: agrega nuevos archivos (alineados por índice).\n"
            "- `delete_media_ids`: elimina media por IDs (solo los que pertenezcan a esta property)."
        ),
        manual_parameters=[
            openapi.Parameter("existing_media", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array de media existente a actualizar. Ej: [{"id":5,"title":"Sala","label":"interior","order":2,"media_type":"image"}]'),
            openapi.Parameter("media_files", openapi.IN_FORM, type=openapi.TYPE_FILE, required=False,
                description="Nuevos archivos de media (múltiples)"),
            openapi.Parameter("media_metadata", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array alineado con media_files. Ej: [{"title":"Fachada","order":1,"media_type":"image"}]'),
            openapi.Parameter("delete_media_ids", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array de IDs a eliminar. Ej: [3, 7]'),
        ],
        consumes=["multipart/form-data"],
    )
    def partial_update(self, request, *args, **kwargs):
        prop = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])

        try:
            existing_media   = json.loads(request.data.get("existing_media",   "[]") or "[]")
            media_metadata   = json.loads(request.data.get("media_metadata",   "[]") or "[]")
            delete_media_ids = json.loads(request.data.get("delete_media_ids", "[]") or "[]")
        except json.JSONDecodeError as exc:
            raise ValidationError({"detail": f"JSON inválido: {exc}"})

        media_files = request.FILES.getlist("media_files")

        if len(media_files) != len(media_metadata):
            raise ValidationError({
                "detail": f"media_files tiene {len(media_files)} archivos pero media_metadata tiene {len(media_metadata)} entradas."
            })

        with transaction.atomic():
            if delete_media_ids:
                PropertyMedia.objects.filter(id__in=delete_media_ids, property=prop).delete()

            for item in existing_media:
                media_id = item.get("id")
                if not media_id:
                    continue
                try:
                    media_obj = PropertyMedia.objects.get(id=media_id, property=prop)
                except PropertyMedia.DoesNotExist:
                    raise ValidationError({"detail": f"El media {media_id} no pertenece a esta propiedad."})
                for field in ("title", "label", "order", "media_type"):
                    if field in item:
                        setattr(media_obj, field, item[field])
                media_obj.save()

            for file, meta in zip(media_files, media_metadata):
                PropertyMedia.objects.create(
                    property=prop,
                    file=file,
                    media_type=meta.get("media_type", "image"),
                    title=meta.get("title"),
                    label=meta.get("label"),
                    order=meta.get("order", 0),
                )

        prop.refresh_from_db()
        return Response(PropertyWithMediaSerializer(prop).data)
