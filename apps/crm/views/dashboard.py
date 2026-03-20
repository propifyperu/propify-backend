from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.crm.models import Contact, Requirement
from apps.properties.models import Property

_TAGS = ["Dashboard"]

_counts_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "properties": openapi.Schema(type=openapi.TYPE_INTEGER),
        "requirements": openapi.Schema(type=openapi.TYPE_INTEGER),
        "contacts": openapi.Schema(type=openapi.TYPE_INTEGER),
    },
)


class DashboardViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Obtener contadores del dashboard",
        operation_description="Devuelve los totales de propiedades, requerimientos y contactos.",
        responses={200: _counts_response},
    )
    @action(detail=False, methods=["get"])
    def counts(self, request):
        return Response({
            "properties": Property.objects.count(),
            "requirements": Requirement.objects.count(),
            "contacts": Contact.objects.count(),
        })
