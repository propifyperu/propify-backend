from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer

_TAGS = ["Notifications"]


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Listar mis notificaciones")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener notificación")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Marcar notificación como leída",
        operation_description="Solo permite actualizar `is_read`.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Obtener mis notificaciones",
        operation_description="Devuelve las últimas 10 notificaciones del usuario autenticado.",
    )
    @action(detail=False, methods=["get"], url_path="my-notifications")
    def my_notifications(self, request):
        qs = (
            Notification.objects
            .filter(user=request.user)
            .order_by("-created_at")[:10]
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
