from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.users.models import Area
from apps.users.serializers import AreaSerializer

_TAGS = ["Users"]


class AreaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar áreas")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener área")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
