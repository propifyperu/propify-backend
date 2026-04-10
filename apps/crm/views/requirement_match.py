from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.crm.filters import RequirementMatchFilter
from apps.crm.models import RequirementMatch
from apps.crm.serializers import RequirementMatchSerializer


class RequirementMatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        RequirementMatch.objects
        .select_related("requirement", "property","property__district","property__currency")
        .prefetch_related("property__media")
        .filter(is_active=True)
        .order_by("-score")
    )
    serializer_class = RequirementMatchSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]

    @swagger_auto_schema(
        tags=["CRM"],
        operation_summary="Listar coincidencias de requerimientos",
        manual_parameters=[
            openapi.Parameter(
                "requirement_id",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="ID del requerimiento para filtrar sus coincidencias",
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        self.queryset = RequirementMatchFilter(
            request.query_params, queryset=self.get_queryset(), request=request
        ).qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Obtener coincidencia de requerimiento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)