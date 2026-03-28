import json

from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.properties.models import Property, PropertyDocument
from apps.properties.serializers.property_document import PropertyDocumentSerializer, PropertyWithDocumentsSerializer


def _is_legal(user):
    try:
        return user.role.area.name.lower() == "legal"
    except AttributeError:
        return False


class PropertyDocumentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Property.objects.prefetch_related("documents")
    serializer_class = PropertyWithDocumentsSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Listar propiedades con documentos")
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(documents__isnull=False).distinct()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(PropertyWithDocumentsSerializer(page, many=True).data)
        return Response(PropertyWithDocumentsSerializer(qs, many=True).data)

    @swagger_auto_schema(tags=["Propiedades"], operation_summary="Obtener propiedad con documentos por property_id")
    def retrieve(self, request, *args, **kwargs):
        prop = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        return Response(PropertyWithDocumentsSerializer(prop).data)

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Crear documentos para una propiedad",
        operation_description=(
            "Crea múltiples documentos para una propiedad en una transacción atómica.\n\n"
            "`documents_metadata` es un JSON array alineado por índice con `document_files`."
        ),
        manual_parameters=[
            openapi.Parameter("property", openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=True,
                description="ID de la propiedad"),
            openapi.Parameter("document_files", openapi.IN_FORM, type=openapi.TYPE_FILE, required=True,
                description="Archivos de documento (se permiten múltiples)"),
            openapi.Parameter("documents_metadata", openapi.IN_FORM, type=openapi.TYPE_STRING, required=True,
                description='JSON array alineado con document_files. Ej: [{"document_type":1,"valid_from":"2026-01-01","status":"vigente","notes":"..."}]'),
        ],
        consumes=["multipart/form-data"],
    )
    def create(self, request, *args, **kwargs):
        prop = get_object_or_404(Property, pk=request.data.get("property"))

        try:
            documents_metadata = json.loads(request.data.get("documents_metadata", "[]") or "[]")
        except json.JSONDecodeError as exc:
            raise ValidationError({"documents_metadata": f"JSON inválido: {exc}"})

        document_files = request.FILES.getlist("document_files")

        if len(document_files) != len(documents_metadata):
            raise ValidationError({
                "detail": f"document_files tiene {len(document_files)} archivos pero documents_metadata tiene {len(documents_metadata)} entradas."
            })

        with transaction.atomic():
            created = [
                PropertyDocument.objects.create(
                    property=prop,
                    file=file,
                    document_type_id=meta.get("document_type"),
                    valid_from=meta.get("valid_from"),
                    valid_to=meta.get("valid_to"),
                    status=meta.get("status"),
                    notes=meta.get("notes"),
                )
                for file, meta in zip(document_files, documents_metadata)
            ]

        return Response(PropertyDocumentSerializer(created, many=True).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Actualizar documentos de una propiedad por property_id",
        operation_description=(
            "Actualiza documentos de una propiedad en lote dentro de una transacción atómica.\n\n"
            "- `existing_documents`: actualiza metadata de documentos existentes (no reemplaza el archivo).\n"
            "- `document_files` + `documents_metadata`: agrega nuevos archivos (alineados por índice).\n"
            "- `delete_document_ids`: elimina documentos por IDs (solo los que pertenezcan a esta property).\n\n"
            "Permisos: usuarios del área Legal pueden editar/eliminar cualquier documento. "
            "El resto solo puede gestionar documentos que hayan creado ellos mismos."
        ),
        manual_parameters=[
            openapi.Parameter("existing_documents", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array de documentos existentes a actualizar. Ej: [{"id":2,"status":"vencido","valid_to":"2026-12-31"}]'),
            openapi.Parameter("document_files", openapi.IN_FORM, type=openapi.TYPE_FILE, required=False,
                description="Nuevos archivos de documento (múltiples)"),
            openapi.Parameter("documents_metadata", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array alineado con document_files. Ej: [{"document_type":1,"status":"vigente"}]'),
            openapi.Parameter("delete_document_ids", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array de IDs a eliminar. Ej: [1, 4]'),
        ],
        consumes=["multipart/form-data"],
    )
    def partial_update(self, request, *args, **kwargs):
        prop = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])

        try:
            existing_documents  = json.loads(request.data.get("existing_documents",  "[]") or "[]")
            documents_metadata  = json.loads(request.data.get("documents_metadata",  "[]") or "[]")
            delete_document_ids = json.loads(request.data.get("delete_document_ids", "[]") or "[]")
        except json.JSONDecodeError as exc:
            raise ValidationError({"detail": f"JSON inválido: {exc}"})

        document_files = request.FILES.getlist("document_files")

        if len(document_files) != len(documents_metadata):
            raise ValidationError({
                "detail": f"document_files tiene {len(document_files)} archivos pero documents_metadata tiene {len(documents_metadata)} entradas."
            })

        is_legal = _is_legal(request.user)

        # --- Validación de permisos antes de mutar ---
        if not is_legal:
            for item in existing_documents:
                doc_id = item.get("id")
                if not doc_id:
                    continue
                try:
                    doc = PropertyDocument.objects.get(id=doc_id, property=prop)
                except PropertyDocument.DoesNotExist:
                    raise ValidationError({"detail": f"El documento {doc_id} no pertenece a esta propiedad."})
                if doc.created_by_id != request.user.id:
                    raise PermissionDenied(f"No tienes permiso para editar el documento {doc_id}.")

            if delete_document_ids:
                restricted = PropertyDocument.objects.filter(
                    id__in=delete_document_ids,
                    property=prop,
                ).exclude(created_by=request.user)
                if restricted.exists():
                    ids = list(restricted.values_list("id", flat=True))
                    raise PermissionDenied(f"No tienes permiso para eliminar los documentos: {ids}.")

        with transaction.atomic():
            if delete_document_ids:
                PropertyDocument.objects.filter(id__in=delete_document_ids, property=prop).delete()

            for item in existing_documents:
                doc_id = item.get("id")
                if not doc_id:
                    continue
                try:
                    doc = PropertyDocument.objects.get(id=doc_id, property=prop)
                except PropertyDocument.DoesNotExist:
                    raise ValidationError({"detail": f"El documento {doc_id} no pertenece a esta propiedad."})
                for field in ("document_type_id", "valid_from", "valid_to", "status", "notes"):
                    src = "document_type" if field == "document_type_id" else field
                    if src in item:
                        setattr(doc, field, item[src])
                doc.save()

            for file, meta in zip(document_files, documents_metadata):
                PropertyDocument.objects.create(
                    property=prop,
                    file=file,
                    document_type_id=meta.get("document_type"),
                    valid_from=meta.get("valid_from"),
                    valid_to=meta.get("valid_to"),
                    status=meta.get("status"),
                    notes=meta.get("notes"),
                )

        prop.refresh_from_db()
        return Response(PropertyWithDocumentsSerializer(prop).data)
