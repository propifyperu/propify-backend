from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.crm.models import RequirementMatch
from apps.crm.serializers import RequirementMatchSerializer


class RequirementMatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RequirementMatchSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        qs = RequirementMatch.objects.select_related(
            "property", "requirement"
        ).filter(is_active=True).order_by("-score")

        requirement_id = self.request.query_params.get("requirement_id")
        if requirement_id:
            qs = qs.filter(requirement_id=requirement_id)

        return qs

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Listar coincidencias de requerimientos",
        manual_parameters=[
            openapi.Parameter(
                "requirement_id",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="ID del requerimiento para filtrar sus coincidencias",
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Obtener coincidencia de requerimiento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)