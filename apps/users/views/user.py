from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.users.filters import UserFilter
from apps.users.models import User
from apps.users.serializers import UserSerializer

_TAGS = ["Users"]


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.select_related("role").all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Listar usuarios",
        operation_description="Devuelve usuarios y permite filtrado por rol, estado activo e información básica de búsqueda.",
        manual_parameters=[
            openapi.Parameter("role",      openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="ID o IDs separados por coma"),
            openapi.Parameter("is_active", openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description="true / false"),
            openapi.Parameter("search",    openapi.IN_QUERY, type=openapi.TYPE_STRING,  description="Busca en first_name, last_name, username, email"),
        ],
    )
    def list(self, request, *args, **kwargs):
        filterset = UserFilter(request.query_params, queryset=self.get_queryset(), request=request)
        self.queryset = filterset.qs
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener usuario")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Actualizar usuario parcialmente")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
