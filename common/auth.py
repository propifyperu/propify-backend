from django.conf import settings
from rest_framework.authentication import BaseAuthentication

_LOCAL_SKIP_PREFIXES = ("/admin/", "/swagger/", "/redoc/")


class LocalModeAuthentication(BaseAuthentication):
    """
    Autenticación de desarrollo: solo activa cuando LOCAL_MODE=True.
    Si el header 'X-User-Id' o 'User-Id' viene en la request, busca o crea
    el usuario correspondiente y lo autentica sin JWT.
    """

    def authenticate(self, request):
        if not getattr(settings, "LOCAL_MODE", False):
            return None

        path = request.path
        if any(path.startswith(p) for p in _LOCAL_SKIP_PREFIXES):
            return None

        user_id = (
            request.META.get("HTTP_X_USER_ID")
            or request.META.get("HTTP_USER_ID")
        )
        if not user_id:
            return None

        from apps.users.models import User  # import tardío para evitar circular

        if "@" in user_id:
            user, _ = User.objects.get_or_create(
                email=user_id,
                defaults={"username": user_id},
            )
        else:
            user, _ = User.objects.get_or_create(
                username=user_id,
                defaults={"email": f"{user_id}@local.test"},
            )

        return (user, None)
