import json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.properties.filters import PropertyCardFilter
from apps.properties.models import Property, PropertyDocument, PropertyFinancialInfo, PropertyMedia, PropertySpecs
from apps.properties.pagination import PropertyCardPagination
from apps.properties.serializers import PropertySerializer
from apps.properties.serializers.property import (
    PropertyCardSerializer,
    PropertyFullDetailSerializer,
    PropertyLandingDetailSerializer,
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
        operation_description="Devuelve propiedades paginadas y permite filtrado por catálogos, búsqueda simple, precio, specs y ubicación.",
        manual_parameters=[
            openapi.Parameter("property_type",      openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
            openapi.Parameter("property_subtype",   openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
            openapi.Parameter("property_condition", openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
            openapi.Parameter("operation_type",     openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
            openapi.Parameter("currency",           openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
            openapi.Parameter("property_status",    openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
            openapi.Parameter("district",           openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
            openapi.Parameter("urbanization",       openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
            openapi.Parameter("responsible",        openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
            openapi.Parameter("search",             openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Busca en code, title, map_address, display_address"),
            openapi.Parameter("price_min",          openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("price_max",          openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("bedrooms_min",       openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter("bathrooms_min",      openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter("land_area_min",      openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("land_area_max",      openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("built_area_min",     openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("built_area_max",     openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("latitude",           openapi.IN_QUERY, type=openapi.TYPE_NUMBER,  description="Latitud del punto central. Requiere longitude y radius_m."),
            openapi.Parameter("longitude",          openapi.IN_QUERY, type=openapi.TYPE_NUMBER,  description="Longitud del punto central. Requiere latitude y radius_m."),
            openapi.Parameter("radius_m",           openapi.IN_QUERY, type=openapi.TYPE_NUMBER,  description="Radio en metros. Filtra propiedades cercanas usando una aproximación por bounding box."),
            openapi.Parameter("created_last_days",  openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Filtra propiedades creadas en los últimos N días. Ej: 7"),
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

        qs = PropertyCardFilter(request.query_params, queryset=qs, request=request).qs

        paginator = PropertyCardPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        if page is not None:
            serializer = PropertyCardSerializer(page, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)

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

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Detalle público de propiedad para landing",
        operation_description="Retorna el detalle público de una propiedad para landing page, buscando por code. No incluye financial ni documents.",
        manual_parameters=[
            openapi.Parameter(
                "code", openapi.IN_QUERY,
                description="Código único de la propiedad (ej: PROP000093)",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
    )
    @action(detail=False, methods=["get"], url_path="landing-detail", permission_classes=[AllowAny])
    def landing_detail(self, request):
        code = request.query_params.get("code")
        if not code:
            return Response({"detail": "El parámetro 'code' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = (
                Property.objects
                .select_related(
                    "property_type", "property_subtype", "property_condition",
                    "operation_type", "currency", "payment_method",
                    "district", "urbanization", "property_status", "responsible",
                    "specs",
                )
                .prefetch_related("media")
                .exclude(property_status_id=6)
                .get(code=code)
            )
        except Property.DoesNotExist:
            return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PropertyLandingDetailSerializer(instance, context={"request": request})
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Obtener code y title por wp_slug",
        operation_description="Endpoint público que busca una propiedad por wp_slug y devuelve solo code y title.",
        manual_parameters=[
            openapi.Parameter(
                "wp_slug", openapi.IN_QUERY,
                description="Slug de WordPress de la propiedad (ej: propify-97)",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
    )
    @action(detail=False, methods=["get"], url_path="wp", permission_classes=[AllowAny])
    def wp(self, request):
        wp_slug = request.query_params.get("wp_slug")
        if not wp_slug:
            return Response({"detail": "El parámetro 'wp_slug' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = Property.objects.get(wp_slug=wp_slug)
        except Property.DoesNotExist:
            return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"code": instance.code, "title": instance.title})

    # ---------------------------------------------------------------------------
    # Helpers internos
    # ---------------------------------------------------------------------------

    _PROPERTY_STATUS_UNAVAILABLE = 6
    _AREAS_CAN_MARK_UNAVAILABLE = {"gerencia", "tecnologias de la informacion"}

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Marcar propiedad como no disponible",
        operation_description="Cambia el estado de la propiedad a No disponible (id=6) sin eliminar físicamente el registro.",
    )
    @action(detail=True, methods=["patch"], url_path="mark-unavailable")
    def mark_unavailable(self, request, pk=None):
        prop = self.get_object()

        # Permiso: creador o área autorizada
        is_creator = prop.created_by_id == request.user.id
        try:
            area_name = request.user.role.area.name.lower()
        except AttributeError:
            area_name = ""
        is_authorized_area = area_name in self._AREAS_CAN_MARK_UNAVAILABLE

        if not (is_creator or is_authorized_area):
            return Response(
                {"detail": "No tienes permiso para marcar esta propiedad como no disponible."},
                status=status.HTTP_403_FORBIDDEN,
            )

        prop.property_status_id = self._PROPERTY_STATUS_UNAVAILABLE
        prop.save()

        serializer = PropertySerializer(prop, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def _normalize_fks(data, fk_fields):
        """Reemplaza claves FK por su versión *_id en el dict dado."""
        for field in fk_fields:
            if field in data:
                data[f"{field}_id"] = data.pop(field)

    @staticmethod
    def _is_legal(user):
        """Devuelve True si el usuario pertenece al área LEGAL."""
        try:
            return user.role.area.name.lower() == "legal"
        except AttributeError:
            return False

    # ---------------------------------------------------------------------------
    # Action: update-full
    # ---------------------------------------------------------------------------

    @swagger_auto_schema(
        tags=["Propiedades"],
        operation_summary="Actualizar propiedad completa (multipart)",
        operation_description=(
            "Actualiza una propiedad junto con specs, información financiera, media y documentos "
            "en una sola transacción. Permite actualizar metadata existente, agregar nuevos archivos "
            "y eliminar registros por IDs.\n\n"
            "- `existing_media` / `existing_documents`: arrays JSON de registros existentes a actualizar.\n"
            "- `media_files` + `media_metadata` se alinean por índice para nuevos archivos.\n"
            "- `document_files` + `documents_metadata` se alinean por índice para nuevos archivos.\n"
            "- `delete_media_ids` / `delete_document_ids`: arrays JSON de IDs a eliminar."
        ),
        manual_parameters=[
            openapi.Parameter("property", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON string parcial con campos de la propiedad. Ej: {"title": "Nueva casa"}'),
            openapi.Parameter("specs", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON string parcial con specs. Ej: {"bedrooms": 4}'),
            openapi.Parameter("financial_info", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON string parcial con info financiera. Ej: {"commission_final": "3.50"}'),
            openapi.Parameter("existing_media", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array de media existente a actualizar. Ej: [{"id": 5, "title": "Sala", "order": 2}]'),
            openapi.Parameter("media_files", openapi.IN_FORM, type=openapi.TYPE_FILE, required=False,
                description="Nuevos archivos de imagen (múltiples)"),
            openapi.Parameter("media_metadata", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array alineado con media_files. Ej: [{"title": "Fachada", "order": 1, "media_type": "image"}]'),
            openapi.Parameter("delete_media_ids", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array de IDs de media a eliminar. Ej: [3, 7]'),
            openapi.Parameter("existing_documents", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array de documentos existentes a actualizar. Ej: [{"id": 2, "status": "vencido"}]'),
            openapi.Parameter("document_files", openapi.IN_FORM, type=openapi.TYPE_FILE, required=False,
                description="Nuevos archivos de documento (múltiples)"),
            openapi.Parameter("documents_metadata", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array alineado con document_files. Ej: [{"document_type": 1, "status": "vigente"}]'),
            openapi.Parameter("delete_document_ids", openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON array de IDs de documentos a eliminar. Ej: [1, 4]'),
        ],
        consumes=["multipart/form-data"],
    )
    @action(detail=True, methods=["patch"], url_path="update-full")
    def update_full(self, request, pk=None):
        from django.db import transaction

        prop = self.get_object()

        # --- Parseo ---
        try:
            property_data      = json.loads(request.data.get("property",            "{}") or "{}")
            specs_data         = json.loads(request.data.get("specs",               "{}") or "{}")
            financial_data     = json.loads(request.data.get("financial_info",      "{}") or "{}")
            existing_media     = json.loads(request.data.get("existing_media",      "[]") or "[]")
            media_metadata     = json.loads(request.data.get("media_metadata",      "[]") or "[]")
            delete_media_ids   = json.loads(request.data.get("delete_media_ids",    "[]") or "[]")
            existing_documents = json.loads(request.data.get("existing_documents",  "[]") or "[]")
            documents_metadata = json.loads(request.data.get("documents_metadata",  "[]") or "[]")
            delete_doc_ids     = json.loads(request.data.get("delete_document_ids", "[]") or "[]")
        except json.JSONDecodeError as exc:
            return Response({"detail": f"JSON inválido: {exc}"}, status=status.HTTP_400_BAD_REQUEST)

        media_files    = request.FILES.getlist("media_files")
        document_files = request.FILES.getlist("document_files")

        # --- Validaciones de alineación ---
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

        # --- Permisos de documentos ---
        is_legal = self._is_legal(request.user)

        if not is_legal:
            # Verificar edición de documentos existentes
            for item in existing_documents:
                doc_id = item.get("id")
                if doc_id:
                    try:
                        doc = PropertyDocument.objects.get(id=doc_id, property=prop)
                    except PropertyDocument.DoesNotExist:
                        return Response(
                            {"detail": f"El documento {doc_id} no pertenece a esta propiedad."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if doc.created_by_id != request.user.id:
                        return Response(
                            {"detail": f"No tienes permiso para editar el documento {doc_id}."},
                            status=status.HTTP_403_FORBIDDEN,
                        )
            # Verificar eliminación de documentos
            if delete_doc_ids:
                restricted = PropertyDocument.objects.filter(
                    id__in=delete_doc_ids,
                    property=prop,
                ).exclude(created_by=request.user)
                if restricted.exists():
                    ids = list(restricted.values_list("id", flat=True))
                    return Response(
                        {"detail": f"No tienes permiso para eliminar los documentos: {ids}."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

        # --- Normalizar FKs ---
        self._normalize_fks(property_data, [
            "contact", "property_type", "property_subtype", "property_condition",
            "operation_type", "currency", "payment_method", "district",
            "urbanization", "property_status", "responsible",
        ])
        self._normalize_fks(specs_data, [
            "water_service", "energy_service", "drainage_service", "gas_service",
        ])

        with transaction.atomic():
            # --- Property ---
            if property_data:
                for field, value in property_data.items():
                    setattr(prop, field, value)
                prop.save()

            # --- Specs ---
            if specs_data:
                specs, _ = PropertySpecs.objects.get_or_create(property=prop)
                for field, value in specs_data.items():
                    setattr(specs, field, value)
                specs.save()

            # --- FinancialInfo ---
            if financial_data:
                financial, _ = PropertyFinancialInfo.objects.get_or_create(property=prop)
                for field, value in financial_data.items():
                    setattr(financial, field, value)
                financial.save()

            # --- Eliminar media ---
            if delete_media_ids:
                PropertyMedia.objects.filter(id__in=delete_media_ids, property=prop).delete()

            # --- Actualizar media existente (solo metadata) ---
            for item in existing_media:
                media_id = item.get("id")
                if not media_id:
                    continue
                try:
                    media_obj = PropertyMedia.objects.get(id=media_id, property=prop)
                except PropertyMedia.DoesNotExist:
                    return Response(
                        {"detail": f"El media {media_id} no pertenece a esta propiedad."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                for field in ("title", "label", "order", "media_type"):
                    if field in item:
                        setattr(media_obj, field, item[field])
                media_obj.save()

            # --- Crear nuevos media ---
            for file, meta in zip(media_files, media_metadata):
                PropertyMedia.objects.create(
                    property=prop,
                    file=file,
                    media_type=meta.get("media_type", "image"),
                    title=meta.get("title"),
                    label=meta.get("label"),
                    order=meta.get("order", 0),
                )

            # --- Eliminar documentos ---
            if delete_doc_ids:
                PropertyDocument.objects.filter(id__in=delete_doc_ids, property=prop).delete()

            # --- Actualizar documentos existentes (solo metadata) ---
            for item in existing_documents:
                doc_id = item.get("id")
                if not doc_id:
                    continue
                try:
                    doc = PropertyDocument.objects.get(id=doc_id, property=prop)
                except PropertyDocument.DoesNotExist:
                    return Response(
                        {"detail": f"El documento {doc_id} no pertenece a esta propiedad."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                for field in ("document_type_id", "valid_from", "valid_to", "status", "notes"):
                    src = "document_type" if field == "document_type_id" else field
                    if src in item:
                        setattr(doc, field, item[src])
                doc.save()

            # --- Crear nuevos documentos ---
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
        return Response(output.data, status=status.HTTP_200_OK)
