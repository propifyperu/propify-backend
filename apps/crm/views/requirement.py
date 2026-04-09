import uuid

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.crm.filters import RequirementFilter
from apps.crm.models import Requirement
from apps.crm.pagination import RequirementPagination
from apps.crm.serializers import RequirementSerializer
from apps.crm.serializers.requirement import RequirementCreateResponseSerializer
from apps.properties.services.requirement_matching import get_matches

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

    @swagger_auto_schema(tags=["CRM"], operation_summary="Listar requerimientos", manual_parameters=_REQ_FILTER_PARAMS)
    def list(self, request, *args, **kwargs):
        qs = RequirementFilter(request.query_params, queryset=self.get_queryset(), request=request).qs
        self.queryset = qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Obtener requerimiento")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Crear requerimiento")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        requirement = serializer.save(
            assigned_to=serializer.validated_data.get("assigned_to") or request.user,
            import_batch="manual",
            import_row_sig=uuid.uuid4().hex,
            source_date=timezone.localdate(),
        )

        # Correr el motor de matching
        get_matches(requirement)

        # Recargar con matches para el response
        requirement = (
            Requirement.objects
            .prefetch_related("requirement_matches", "districts", "urbanizations")
            .select_related(
                "lead", "assigned_to", "operation_type", "property_type",
                "property_subtype", "property_condition", "currency", "payment_method",
            )
            .get(pk=requirement.pk)
        )

        output = RequirementCreateResponseSerializer(requirement, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Mis requerimientos", manual_parameters=[p for p in _REQ_FILTER_PARAMS if p.name != "assigned_to"])
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
        return Response(self.get_serializer(qs, many=True).data)

    @swagger_auto_schema(tags=["CRM"], operation_summary="Actualizar requerimiento parcialmente")
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)