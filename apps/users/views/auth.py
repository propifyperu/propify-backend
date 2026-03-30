from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.serializers import UserMeSerializer

User = get_user_model()

_TAGS = ["Auth"]


# ---------------------------------------------------------------------------
# Permitir login con email además de username
# ---------------------------------------------------------------------------

class EmailOrUsernameTokenSerializer(TokenObtainPairSerializer):
    """
    Si el campo username contiene '@', busca el usuario por email
    y reemplaza el valor por su username antes de la validación JWT.
    """

    def validate(self, attrs):
        credential = attrs.get(self.username_field, "")
        if "@" in credential:
            try:
                user = User.objects.get(email=credential)
                attrs[self.username_field] = user.username
            except User.DoesNotExist:
                pass
        data = super().validate(attrs)
        data["id"] = self.user.id
        data["username"] = self.user.username
        data["name"] = self.user.get_full_name() or self.user.username
        data["role"] = self.user.role.name if self.user.role_id else None
        data["area"] = self.user.role.area.name if self.user.role_id else None
        return data


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

_token_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["username", "password"],
    properties={
        "username": openapi.Schema(type=openapi.TYPE_STRING, description="Usuario o email"),
        "password": openapi.Schema(type=openapi.TYPE_STRING),
    },
)

_token_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "access": openapi.Schema(type=openapi.TYPE_STRING),
        "refresh": openapi.Schema(type=openapi.TYPE_STRING),
        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
        "username": openapi.Schema(type=openapi.TYPE_STRING),
        "name": openapi.Schema(type=openapi.TYPE_STRING),
        "role": openapi.Schema(type=openapi.TYPE_STRING),
        "area": openapi.Schema(type=openapi.TYPE_STRING),
    },
)


class TokenObtainView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Obtener tokens JWT",
        operation_description="Retorna access y refresh token. El campo `username` acepta nombre de usuario o email.",
        request_body=_token_request_body,
        responses={200: _token_response},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefreshAPIView(TokenRefreshView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Refrescar access token",
        operation_description="Recibe un `refresh` token y devuelve un nuevo `access` token.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Usuario autenticado",
        operation_description="Retorna los datos del usuario autenticado, incluyendo su perfil (`user_profile`) si existe.",
        responses={200: UserMeSerializer()},
    )
    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)
