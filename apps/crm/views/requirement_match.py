from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from apps.crm.models import RequirementMatch
from apps.crm.serializers import RequirementMatchSerializer


class RequirementMatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RequirementMatch.objects.all()
    serializer_class = RequirementMatchSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(tags=["CRM"], operation_summary="Listar coincidencias de requerimientos")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Obtener coincidencia de requerimiento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
