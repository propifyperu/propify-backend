from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.users.models import UserProfile
from apps.users.serializers import UserProfileSerializer

_TAGS = ["Users"]


class UserProfileViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = UserProfile.objects.select_related("user", "country", "city").all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar perfiles de usuario")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener perfil de usuario")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Actualizar perfil parcialmente")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
