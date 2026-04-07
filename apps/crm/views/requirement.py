import uuid

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.crm.filters import RequirementFilter
from apps.crm.models import Requirement
from apps.crm.pagination import RequirementPagination
from apps.crm.serializers import RequirementSerializer

_REQ_FILTER_PARAMS = [
    openapi.Parameter("assigned_to",        openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("lead",               openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("operation_type",     openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("property_type",      openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("property_subtype",   openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("property_condition", openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("currency",           openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("payment_method",     openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("districts",          openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("urbanizations",      openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("has_elevator",       openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
    openapi.Parameter("pet_friendly",       openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
    openapi.Parameter("date_mode",          openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="day | week | month | range"),
    openapi.Parameter("date",               openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Fecha base ISO (YYYY-MM-DD)"),
    openapi.Parameter("date_from",          openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Fecha inicio ISO (YYYY-MM-DD). Requerida en range."),
    openapi.Parameter("date_to",            openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Fecha fin ISO (YYYY-MM-DD). Requerida en range."),
    openapi.Parameter("ordering",           openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="created_at | -created_at"),
    openapi.Parameter("page",               openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("page_size",          openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Máx 100"),
]


class RequirementViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Requirement.objects.select_related(
        "lead", "assigned_to", "operation_type", "property_type",
        "property_subtype", "property_condition", "currency", "payment_method",
    ).prefetch_related("districts", "urbanizations").all()
    serializer_class = RequirementSerializer
    pagination_class = RequirementPagination
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Listar requerimientos",
        manual_parameters=_REQ_FILTER_PARAMS,
    )
    def list(self, request, *args, **kwargs):
        qs = RequirementFilter(request.query_params, queryset=self.get_queryset(), request=request).qs
        self.queryset = qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Obtener requerimiento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Crear requerimiento",
        operation_description=(
            "Crea un requerimiento de búsqueda.\n\n"
            "**Obligatorios:** `operation_type`, `property_type`, `districts` (mínimo 1), "
            "`price_min`, `price_max`.\n\n"
            "**Opcionales:** `lead`, `assigned_to`, `property_subtype`, `property_condition`, "
            "`currency`, `payment_method`, `urbanizations`, rangos de área/habitaciones/etc., "
            "`has_elevator`, `pet_friendly`, `notes`.\n\n"
            "**No enviar:** `source_group`, `source_date`, `notes_message_ws`, `import_batch`, "
            "`import_row_sig`, `is_active` (se gestionan automáticamente).\n\n"
            "- Si `assigned_to` no se envía, se asigna el usuario autenticado.\n"
            "- `import_batch` se fija en `manual`; `import_row_sig` se genera como UUID.\n"
            "- `source_date` se asigna con la fecha actual.\n"
            "- Todos los pares min/max deben cumplir `min ≤ max`."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["operation_type", "property_type", "districts", "price_min", "price_max"],
            properties={
                "operation_type":    openapi.Schema(type=openapi.TYPE_INTEGER),
                "property_type":     openapi.Schema(type=openapi.TYPE_INTEGER),
                "districts":         openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER), description="Mínimo 1"),
                "price_min":         openapi.Schema(type=openapi.TYPE_NUMBER),
                "price_max":         openapi.Schema(type=openapi.TYPE_NUMBER),
                "lead":              openapi.Schema(type=openapi.TYPE_INTEGER),
                "assigned_to":       openapi.Schema(type=openapi.TYPE_INTEGER, description="Si no se envía, se usa el usuario autenticado"),
                "property_subtype":  openapi.Schema(type=openapi.TYPE_INTEGER),
                "property_condition":openapi.Schema(type=openapi.TYPE_INTEGER),
                "currency":          openapi.Schema(type=openapi.TYPE_INTEGER),
                "payment_method":    openapi.Schema(type=openapi.TYPE_INTEGER),
                "urbanizations":     openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)),
                "bedrooms_min":      openapi.Schema(type=openapi.TYPE_NUMBER),
                "bedrooms_max":      openapi.Schema(type=openapi.TYPE_NUMBER),
                "bathrooms_min":     openapi.Schema(type=openapi.TYPE_NUMBER),
                "bathrooms_max":     openapi.Schema(type=openapi.TYPE_NUMBER),
                "built_area_min":    openapi.Schema(type=openapi.TYPE_NUMBER),
                "built_area_max":    openapi.Schema(type=openapi.TYPE_NUMBER),
                "land_area_min":     openapi.Schema(type=openapi.TYPE_NUMBER),
                "land_area_max":     openapi.Schema(type=openapi.TYPE_NUMBER),
                "floors_min":        openapi.Schema(type=openapi.TYPE_NUMBER),
                "floors_max":        openapi.Schema(type=openapi.TYPE_NUMBER),
                "antiquity_years_min": openapi.Schema(type=openapi.TYPE_NUMBER),
                "antiquity_years_max": openapi.Schema(type=openapi.TYPE_NUMBER),
                "garage_spaces_min": openapi.Schema(type=openapi.TYPE_NUMBER),
                "garage_spaces_max": openapi.Schema(type=openapi.TYPE_NUMBER),
                "has_elevator":      openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "pet_friendly":      openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "notes":             openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            assigned_to=serializer.validated_data.get("assigned_to") or self.request.user,
            import_batch="manual",
            import_row_sig=uuid.uuid4().hex,
            source_date=timezone.localdate(),
        )

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Mis requerimientos",
        operation_description="Devuelve solo los requerimientos asignados al usuario autenticado (`assigned_to`). Soporta los mismos filtros que el listado general, excepto `assigned_to`.",
        manual_parameters=[p for p in _REQ_FILTER_PARAMS if p.name != "assigned_to"],
    )
    @action(detail=False, methods=["get"], url_path="my-requirements")
    def my_requirements(self, request):
        base_qs = self.get_queryset().filter(assigned_to=request.user)
        params = request.query_params.copy()
        params.pop("assigned_to", None)
        qs = RequirementFilter(params, queryset=base_qs, request=request).qs
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Actualizar requerimiento parcialmente",
        operation_description=(
            "Actualiza parcialmente un requerimiento. Todos los campos son opcionales.\n\n"
            "Los pares min/max deben cumplir `min ≤ max`. Si solo se envía uno de los dos, "
            "se valida contra el valor actual de la instancia."
        ),
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
