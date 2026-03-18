from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.users.models import Role
from apps.users.serializers import RoleSerializer

_TAGS = ["Users"]


class RoleViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Role.objects.select_related("area").all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar roles")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener rol")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
