from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.crm.filters import LeadFilter
from apps.crm.models import Lead
from apps.crm.pagination import LeadPagination
from apps.crm.serializers import LeadSerializer

_LEAD_FILTER_PARAMS = [
    openapi.Parameter("assigned_to",     openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("lead_status",     openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("canal_lead",      openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("operation_types", openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("properties",      openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
    openapi.Parameter("full_name",       openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Búsqueda parcial por nombre"),
    openapi.Parameter("phone",           openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Búsqueda parcial por teléfono"),
    openapi.Parameter("username",        openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Búsqueda parcial por username"),
    openapi.Parameter("date_mode",       openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="day | week | month | range"),
    openapi.Parameter("date",            openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Fecha base ISO (YYYY-MM-DD)"),
    openapi.Parameter("date_from",       openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Fecha inicio ISO (YYYY-MM-DD). Requerida en range."),
    openapi.Parameter("date_to",         openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Fecha fin ISO (YYYY-MM-DD). Requerida en range."),
    openapi.Parameter("ordering",        openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="date_entry | -date_entry | full_name | -full_name"),
    openapi.Parameter("page",            openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("page_size",       openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Máx 100"),
]


class LeadViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Lead.objects.select_related(
        "lead_status", "canal_lead", "assigned_to",
    ).prefetch_related("operation_types", "properties").all()
    serializer_class = LeadSerializer
    pagination_class = LeadPagination
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @swagger_auto_schema(tags=["CRM"], operation_summary="Listar leads", manual_parameters=_LEAD_FILTER_PARAMS)
    def list(self, request, *args, **kwargs):
        qs = LeadFilter(request.query_params, queryset=self.get_queryset(), request=request).qs
        self.queryset = qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Obtener lead")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Crear lead")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        lead_status = serializer.validated_data.get("lead_status")
        if not lead_status:
            from apps.catalogs.models import LeadStatus
            lead_status = LeadStatus.objects.filter(name="Nuevo").first()
            if not lead_status:
                raise ValidationError({"lead_status": "No existe estado inicial 'Nuevo'."})

        assigned_to = serializer.validated_data.get("assigned_to") or self.request.user
        serializer.save(assigned_to=assigned_to, lead_status=lead_status)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Actualizar lead parcialmente")
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Mis leads",
        operation_description="Devuelve solo los leads asignados al usuario autenticado (`assigned_to`). Soporta los mismos filtros que el listado general, excepto `assigned_to`.",
        manual_parameters=[p for p in _LEAD_FILTER_PARAMS if p.name != "assigned_to"],
    )
    @action(detail=False, methods=["get"], url_path="my-leads")
    def my_leads(self, request):
        base_qs = self.get_queryset().filter(assigned_to=request.user)
        params = request.query_params.copy()
        params.pop("assigned_to", None)
        qs = LeadFilter(params, queryset=base_qs, request=request).qs
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
