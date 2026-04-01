from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.decorators import action
from apps.crm.models import Contact
from apps.crm.serializers import ContactSerializer
from rest_framework.response import Response


class ContactViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Contact.objects.prefetch_related("assigned_agent").all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @swagger_auto_schema(tags=["CRM"], operation_summary="Listar contactos")
    def list(self, request, *args, **kwargs):
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

    @swagger_auto_schema(tags=["CRM"], operation_summary="Actualizar contacto parcialmente")
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Listar mis contactos",
        operation_description="Retorna solo los contactos cuyo assigned_agent es el usuario autenticado.",
    )
    
    @action(detail=False, methods=["get"], url_path="my-contacts")
    def my_contacts(self, request):
        qs = Contact.objects.filter(assigned_agent=request.user).order_by("first_name")
        serializer = ContactSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)