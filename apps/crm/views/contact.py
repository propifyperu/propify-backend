from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.crm.filters import ContactFilter
from apps.crm.models import Contact
from apps.crm.pagination import ContactPagination
from apps.crm.serializers import ContactSerializer

_CONTACT_FILTER_PARAMS = [
    openapi.Parameter("full_name",     openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Busca en first_name y last_name"),
    openapi.Parameter("email",         openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Búsqueda parcial por email"),
    openapi.Parameter("phone",         openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Búsqueda parcial por teléfono"),
    openapi.Parameter("document_type", openapi.IN_QUERY, type=openapi.TYPE_STRING, description="dni | passport | ce"),
    openapi.Parameter("ordering",      openapi.IN_QUERY, type=openapi.TYPE_STRING, description="created_at | -created_at"),
]


class ContactViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Contact.objects.prefetch_related("assigned_agent").all()
    serializer_class = ContactSerializer
    pagination_class = ContactPagination
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    @swagger_auto_schema(tags=["CRM"], operation_summary="Listar contactos", manual_parameters=_CONTACT_FILTER_PARAMS)
    def list(self, request, *args, **kwargs):
        qs = ContactFilter(request.query_params, queryset=self.get_queryset(), request=request).qs
        self.queryset = qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Obtener contacto")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Crear contacto",
        operation_description=(
            "Crea un contacto. Soporta multipart/form-data para enviar `photo` como archivo.\n\n"
            "El usuario autenticado se asigna automáticamente como `assigned_agent`; "
            "no es necesario (ni posible) enviarlo desde el frontend."
        ),
        consumes=["multipart/form-data"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        contact = serializer.save()
        contact.assigned_agent.add(self.request.user)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Actualizar contacto parcialmente",
        operation_description=(
            "Actualiza parcialmente un contacto. Soporta multipart/form-data.\n\n"
            "- `photo` puede enviarse como archivo; si no se envía, la foto actual no se modifica.\n"
            "- `assigned_agent` no puede editarse desde este endpoint; se ignora si viene en el request."
        ),
        consumes=["multipart/form-data"],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Eliminar contacto",
        operation_description=(
            "Si el contacto está asignado a más de un agente, solo se quita la asignación del usuario autenticado.\n\n"
            "Si el contacto está asignado a un único agente (o ninguno), se elimina físicamente."
        ),
        responses={
            200: "Contacto eliminado correctamente. / Asignación removida (el contacto tiene otros agentes asignados).",
        },
    )
    def destroy(self, request, *args, **kwargs):
        contact = self.get_object()
        agent_count = contact.assigned_agent.count()

        if agent_count > 1:
            contact.assigned_agent.remove(request.user)
            return Response(
                {"detail": "Asignación removida. El contacto permanece asignado a otros agentes."},
                status=status.HTTP_200_OK,
            )

        contact.delete()
        return Response(
            {"detail": "Contacto eliminado correctamente."},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Listar mis contactos",
        operation_description="Retorna solo los contactos asignados al usuario autenticado. Soporta los mismos filtros que el listado general.",
        manual_parameters=_CONTACT_FILTER_PARAMS,
    )
    @action(detail=False, methods=["get"], url_path="my-contacts")
    def my_contacts(self, request):
        base_qs = self.get_queryset().filter(assigned_agent=request.user)
        qs = ContactFilter(request.query_params, queryset=base_qs, request=request).qs
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)