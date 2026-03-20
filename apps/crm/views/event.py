from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.crm.models import Event
from apps.crm.serializers import EventSerializer


class EventViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @swagger_auto_schema(tags=["CRM"], operation_summary="Listar eventos")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Obtener evento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Crear evento")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Actualizar evento parcialmente")
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Obtener mis eventos",
        operation_description="Devuelve los eventos asignados al usuario autenticado, ordenados por fecha de inicio.",
    )
    @action(detail=False, methods=["get"], url_path="my-events")
    def my_events(self, request):
        qs = (
            Event.objects
            .filter(assigned_agent=request.user)
            .select_related("event_type", "assigned_agent", "lead", "contact", "property")
            .order_by("start_time")
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
