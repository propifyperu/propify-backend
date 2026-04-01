import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.filters import UserFilter
from apps.users.models import User
from apps.users.serializers.user import UserDetailSerializer

_TAGS = ["Users"]


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.select_related("role", "profile", "settings").all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "patch", "head", "options"]

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Listar usuarios",
        operation_description="Devuelve usuarios con profile y settings. Permite filtrado por rol, estado activo e información básica de búsqueda.",
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

    @swagger_auto_schema(tags=_TAGS, operation_summary="Obtener usuario",
                         operation_description="Retorna el usuario con profile y settings anidados.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Actualizar usuario parcialmente",
        operation_description=(
            "Actualiza User, UserProfile y UserSettings en un solo request. "
            "Soporta multipart/form-data.\n\n"
            "- Campos de `User` van directos en form-data.\n"
            "- `profile` como JSON string (ej: `{\"phone\": \"999\"}`).\n"
            "- `settings` como JSON string (ej: `{\"theme\": \"dark\"}`).\n"
            "- `avatar_url` como archivo.\n\n"
            "Crea `profile` y `settings` si no existen."
        ),
        manual_parameters=[
            openapi.Parameter("profile",    openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON string con campos de UserProfile. Ej: {"phone": "999", "address": "Lima"}'),
            openapi.Parameter("settings",   openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                description='JSON string con campos de UserSettings. Ej: {"theme": "dark", "language": "es"}'),
            openapi.Parameter("avatar_url", openapi.IN_FORM, type=openapi.TYPE_FILE,   required=False,
                description="Archivo de avatar del usuario"),
        ],
        consumes=["multipart/form-data"],
    )
    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()

        # --- Parseo ---
        try:
            profile_data  = json.loads(request.data.get("profile",  "{}") or "{}")
            settings_data = json.loads(request.data.get("settings", "{}") or "{}")
        except json.JSONDecodeError as exc:
            return Response({"detail": f"JSON inválido: {exc}"}, status=status.HTTP_400_BAD_REQUEST)

        avatar_file = request.FILES.get("avatar_url")

        # --- Campos de User ---
        user_fields = {"first_name", "last_name", "email", "username", "is_active", "is_staff", "role"}
        user_data = {k: v for k, v in request.data.items() if k in user_fields}
        if "role" in user_data:
            user.role_id = user_data.pop("role")
        if "country" in profile_data:
            profile_data["country_id"] = profile_data.pop("country")
        if "city" in profile_data:
            profile_data["city_id"] = profile_data.pop("city")
        for field, value in user_data.items():
            setattr(user, field, value)
        if user_data or "role" in request.data:
            user.save()

        # --- Profile ---
        if profile_data or avatar_file:
            from apps.users.models.user_profile import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            for field, value in profile_data.items():
                setattr(profile, field, value)
            if avatar_file:
                profile.avatar_url = avatar_file
            profile.save()

        # --- Settings ---
        if settings_data:
            from apps.users.models.settings import UserSettings
            settings_obj, _ = UserSettings.objects.get_or_create(user=user)
            for field, value in settings_data.items():
                setattr(settings_obj, field, value)
            settings_obj.save()

        user.refresh_from_db()
        serializer = UserDetailSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
