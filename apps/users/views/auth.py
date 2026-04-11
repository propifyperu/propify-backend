import os

from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.models import UserProfile
from apps.users.serializers import UserDetailSerializer, UserMeSerializer
from apps.users.serializers.auth import GoogleLoginSerializer

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
        data["external_id"] = self.user.external_id
        data["name"] = self.user.get_full_name() or self.user.username
        data["role"] = self.user.role.name if self.user.role_id else None
        data["area"] = self.user.role.area.name if self.user.role_id else None
        try:
            avatar = self.user.profile.avatar_url
            data["avatar_url"] = avatar.url if avatar else None
        except Exception:
            data["avatar_url"] = None
        return data


# ---------------------------------------------------------------------------
# Swagger schemas
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
        "external_id": openapi.Schema(type=openapi.TYPE_STRING),
        "name": openapi.Schema(type=openapi.TYPE_STRING),
        "role": openapi.Schema(type=openapi.TYPE_STRING),
        "area": openapi.Schema(type=openapi.TYPE_STRING),
        "avatar_url": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="URL del avatar del usuario, o null si no tiene",
        ),
    },
)

_google_login_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["id_token"],
    properties={
        "id_token": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Token de Google Identity Services",
        ),
    },
)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

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


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Login con Google",
        operation_description="Recibe el id_token de Google, lo valida, busca o crea el usuario y devuelve JWT propio.",
        request_body=_google_login_request_body,
        responses={200: _token_response},
    )
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_id_token = serializer.validated_data["id_token"]
        google_client_id = os.environ.get("GOOGLE_CLIENT_ID")

        if not google_client_id:
            return Response(
                {"detail": "GOOGLE_CLIENT_ID no configurado."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            idinfo = google_id_token.verify_oauth2_token(
                raw_id_token,
                google_requests.Request(),
                google_client_id,
            )
        except ValueError:
            return Response(
                {"detail": "Token de Google inválido."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = idinfo.get("email")
        first_name = idinfo.get("given_name", "")
        last_name = idinfo.get("family_name", "")
        picture = idinfo.get("picture")
        google_sub = idinfo.get("sub")
        email_verified = bool(idinfo.get("email_verified", False))

        if not email:
            return Response(
                {"detail": "No se pudo obtener el email de Google."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=email).first()

        if user is None:
            base_username = email.split("@")[0]
            username = base_username
            suffix = 1

            while User.objects.filter(username=username).exists():
                suffix += 1
                username = f"{base_username}{suffix}"

            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                external_id=google_sub,
                email_verified=email_verified,
            )
        else:
            updated_fields = []

            if not user.external_id and google_sub:
                user.external_id = google_sub
                updated_fields.append("external_id")

            if email_verified and not user.email_verified:
                user.email_verified = True
                updated_fields.append("email_verified")

            if first_name and not user.first_name:
                user.first_name = first_name
                updated_fields.append("first_name")

            if last_name and not user.last_name:
                user.last_name = last_name
                updated_fields.append("last_name")

            if updated_fields:
                user.save(update_fields=updated_fields)

        if picture:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if not profile.avatar_url:
                profile.avatar_url = picture
                profile.save(update_fields=["avatar_url"])

        refresh = RefreshToken.for_user(user)

        avatar_url = None
        try:
            avatar = user.profile.avatar_url
            avatar_url = avatar.url if avatar else None
        except Exception:
            avatar_url = picture or None

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "id": user.id,
                "username": user.username,
                "external_id": user.external_id,
                "name": user.get_full_name() or user.username,
                "role": user.role.name if user.role_id else None,
                "area": user.role.area.name if user.role_id else None,
                "avatar_url": avatar_url,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=_TAGS,
        operation_summary="Usuario autenticado",
        operation_description="Retorna los datos del usuario autenticado, incluyendo su perfil (`user_profile`) si existe.",
        responses={200: UserMeSerializer()},
    )
    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)