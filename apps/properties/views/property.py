import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.properties.filters import PropertyCardFilter
from apps.properties.models import Property, PropertyDocument, PropertyFinancialInfo, PropertyMedia, PropertySpecs
from apps.properties.pagination import PropertyCardPagination
from apps.properties.serializers import PropertySerializer
from apps.properties.serializers.property import (
    PropertyCardSerializer,
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
    parser_classes = [MultiPartParser, FormParser]
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
        operation_description="Devuelve propiedades paginadas y permite filtrado por catálogos, búsqueda simple, precio y specs.",
        manual_parameters=[
            openapi.Parameter("property_type",      openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("property_subtype",   openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("property_condition", openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("operation_type",     openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("currency",           openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("property_status",    openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("district",           openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("urbanization",       openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("responsible",        openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("search",             openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Busca en code, title, map_address, display_address"),
            openapi.Parameter("price_min",          openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("price_max",          openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("bedrooms_min",       openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter("bathrooms_min",      openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter("land_area_min",      openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("land_area_max",      openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("built_area_min",     openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("built_area_max",     openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("page",               openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ],
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

        # Filtros
        filterset = PropertyCardFilter(request.query_params, queryset=qs, request=request)
        qs = filterset.qs

        # Paginación específica para cards
        paginator = PropertyCardPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = PropertyCardSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

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
        operation_summary="Crear propiedad completa (multipart)",
        operation_description=(
            "Crea una propiedad junto con specs, info financiera, imágenes y documentos "
            "en una sola transacción atómica. Usar `Content-Type: multipart/form-data`.\n\n"
            "`media_metadata` y `documents_metadata` son JSON arrays donde cada posición "
            "corresponde al archivo del mismo índice en `media_files` / `document_files`."
        ),
        manual_parameters=[
            openapi.Parameter(
                "property", openapi.IN_FORM,
                description='JSON string con los campos de la propiedad. Ej: {"title": "Casa", "contact": 1, ...}',
                type=openapi.TYPE_STRING, required=True,
            ),
            openapi.Parameter(
                "specs", openapi.IN_FORM,
                description='JSON string con los specs (opcional). Ej: {"bedrooms": 3, "bathrooms": 2}',
                type=openapi.TYPE_STRING, required=False,
            ),
            openapi.Parameter(
                "financial_info", openapi.IN_FORM,
                description='JSON string con la info financiera (opcional). Ej: {"commission_initial": "3.00"}',
                type=openapi.TYPE_STRING, required=False,
            ),
            openapi.Parameter(
                "media_files", openapi.IN_FORM,
                description="Archivos de imagen (se permiten múltiples)",
                type=openapi.TYPE_FILE, required=False,
            ),
            openapi.Parameter(
                "media_metadata", openapi.IN_FORM,
                description=(
                    'JSON array string alineado con media_files. '
                    'Ej: [{"title": "Fachada", "label": "principal", "order": 1, "media_type": "image"}]'
                ),
                type=openapi.TYPE_STRING, required=False,
            ),
            openapi.Parameter(
                "document_files", openapi.IN_FORM,
                description="Archivos de documento (se permiten múltiples)",
                type=openapi.TYPE_FILE, required=False,
            ),
            openapi.Parameter(
                "documents_metadata", openapi.IN_FORM,
                description=(
                    'JSON array string alineado con document_files. '
                    'Ej: [{"document_type": 1, "valid_from": "2026-01-01", "status": "vigente", "notes": "..."}]'
                ),
                type=openapi.TYPE_STRING, required=False,
            ),
        ],
        consumes=["multipart/form-data"],
    )
    @action(detail=False, methods=["post"], url_path="create-full")
    def create_full(self, request):
        import uuid as uuid_lib
        from django.db import transaction

        try:
            property_data = json.loads(request.data.get("property", "{}"))
            specs_data = json.loads(request.data.get("specs", "{}") or "{}")
            financial_data = json.loads(request.data.get("financial_info", "{}") or "{}")
            media_metadata = json.loads(request.data.get("media_metadata", "[]") or "[]")
            documents_metadata = json.loads(request.data.get("documents_metadata", "[]") or "[]")
        except json.JSONDecodeError as exc:
            return Response({"detail": f"JSON inválido: {exc}"}, status=status.HTTP_400_BAD_REQUEST)

        media_files = request.FILES.getlist("media_files")
        document_files = request.FILES.getlist("document_files")

        if len(media_files) != len(media_metadata):
            return Response(
                {"detail": f"media_files tiene {len(media_files)} archivos pero media_metadata tiene {len(media_metadata)} entradas."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(document_files) != len(documents_metadata):
            return Response(
                {"detail": f"document_files tiene {len(document_files)} archivos pero documents_metadata tiene {len(documents_metadata)} entradas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normalizar FKs: reemplazar nombre de campo por *_id
        _property_fks = [
            "contact", "property_type", "property_subtype", "property_condition",
            "operation_type", "currency", "payment_method", "district",
            "urbanization", "property_status", "responsible",
        ]
        for field in _property_fks:
            if field in property_data:
                property_data[f"{field}_id"] = property_data.pop(field)

        _specs_fks = ["water_service", "energy_service", "drainage_service", "gas_service"]
        for field in _specs_fks:
            if field in specs_data:
                specs_data[f"{field}_id"] = specs_data.pop(field)

        property_data["uuid"] = uuid_lib.uuid4()

        with transaction.atomic():
            prop = Property.objects.create(**property_data)

            if specs_data:
                PropertySpecs.objects.create(property=prop, **specs_data)

            if financial_data:
                PropertyFinancialInfo.objects.create(property=prop, **financial_data)

            for file, meta in zip(media_files, media_metadata):
                PropertyMedia.objects.create(
                    property=prop,
                    file=file,
                    media_type=meta.get("media_type", "image"),
                    title=meta.get("title"),
                    label=meta.get("label"),
                    order=meta.get("order", 1),
                )

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
        output = PropertyFullDetailSerializer(prop, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)
