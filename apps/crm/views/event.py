from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.crm.filters import EventFilter
from apps.crm.models import Event
from apps.crm.serializers import EventSerializer

_DATE_PARAMS = [
    openapi.Parameter("date_mode",  openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="day | week | month | range"),
    openapi.Parameter("date",       openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Fecha base ISO (YYYY-MM-DD). Requerida en day / week / month."),
    openapi.Parameter("date_from",  openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Fecha inicio ISO (YYYY-MM-DD). Requerida en range."),
    openapi.Parameter("date_to",    openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Fecha fin ISO (YYYY-MM-DD). Requerida en range."),
]


class EventViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Event.objects.select_related(
        "event_type", "assigned_agent", "property", "contact", "lead", "match", "proposal"
    ).all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Listar eventos",
        manual_parameters=[
            openapi.Parameter("assigned_agent", openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("event_type",     openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("property",       openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("status",         openapi.IN_QUERY, type=openapi.TYPE_STRING, description="pending | accepted | rejected"),
            *_DATE_PARAMS,
        ],
    )
    def list(self, request, *args, **kwargs):
        qs = EventFilter(request.query_params, queryset=self.get_queryset(), request=request).qs
        self.queryset = qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Obtener evento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Crear evento",
        operation_description=(
            "Crea un evento de CRM.\n\n"
            "**Campos obligatorios:** `event_type`, `assigned_agent`, `property`, "
            "`title`, `description`, `start_time`, `end_time`.\n\n"
            "**Campos opcionales:** `contact`.\n\n"
            "**No enviar:** `code` (se genera automáticamente), `status` (inicia en `pending`), "
            "`is_active`, `lead`, `match`, `proposal`.\n\n"
            "`end_time` debe ser mayor que `start_time`."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["event_type", "assigned_agent", "property", "title", "description", "start_time", "end_time"],
            properties={
                "event_type":     openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del tipo de evento"),
                "assigned_agent": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del agente asignado"),
                "property":       openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la propiedad"),
                "contact":        openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del contacto (opcional)"),
                "title":          openapi.Schema(type=openapi.TYPE_STRING),
                "description":    openapi.Schema(type=openapi.TYPE_STRING),
                "start_time":     openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                "end_time":       openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            },
        ),
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Actualizar evento parcialmente",
        operation_description=(
            "Actualiza parcialmente un evento de CRM.\n\n"
            "Todos los campos son opcionales en PATCH.\n"
            "Se puede actualizar `tracing` normalmente.\n"
            "Si se envía `start_time` y/o `end_time`, se valida que `end_time` sea mayor que `start_time`.\n\n"
            "**No editar desde este endpoint:** `code`, `status`, `is_active`."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "event_type": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del tipo de evento"),
                "assigned_agent": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del agente asignado"),
                "property": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la propiedad"),
                "contact": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del contacto"),
                "lead": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del lead"),
                "match": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del match"),
                "proposal": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la propuesta"),
                "title": openapi.Schema(type=openapi.TYPE_STRING),
                "description": openapi.Schema(type=openapi.TYPE_STRING),
                "tracing": openapi.Schema(type=openapi.TYPE_STRING),
                "start_time": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                "end_time": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            },
        ),
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Obtener mis eventos",
        operation_description="Devuelve los eventos asignados al usuario autenticado. Soporta los mismos filtros que el listado general, excepto `assigned_agent`.",
        manual_parameters=[
            openapi.Parameter("event_type", openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("property",   openapi.IN_QUERY, type=openapi.TYPE_STRING, description="ID o IDs separados por coma"),
            openapi.Parameter("status",     openapi.IN_QUERY, type=openapi.TYPE_STRING, description="pending | accepted | rejected"),
            *_DATE_PARAMS,
        ],
    )
    @action(detail=False, methods=["get"], url_path="my-events")
    def my_events(self, request):
        base_qs = self.get_queryset().filter(assigned_agent=request.user)
        # Excluir assigned_agent de los query params para que no pueda sobreescribir el filtro base
        params = request.query_params.copy()
        params.pop("assigned_agent", None)
        qs = EventFilter(params, queryset=base_qs, request=request).qs
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
