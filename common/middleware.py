import json
import logging
import time

from common.current_user import clear_current_user, set_current_user

logger = logging.getLogger("propify.requests")

_SENSITIVE = {"authorization", "password", "token", "secret"}
_MAX_BODY = 500


class RequestLoggingMiddleware:
    """
    Registra METHOD PATH → STATUS en Xms.
    En DEBUG, añade el body JSON si es pequeño (máx _MAX_BODY chars).
    Nunca loguea Authorization ni passwords.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t0 = time.monotonic()
        response = self.get_response(request)
        ms = int((time.monotonic() - t0) * 1000)

        extra = ""
        from django.conf import settings
        if settings.DEBUG and request.content_type == "application/json":
            try:
                body = json.loads(request.body.decode("utf-8", errors="ignore"))
                # eliminar campos sensibles
                body = {k: v for k, v in body.items() if k.lower() not in _SENSITIVE}
                text = json.dumps(body, ensure_ascii=False)[:_MAX_BODY]
                extra = f" | body={text}"
            except Exception:
                pass

        logger.info("%s %s → %s (%dms)%s", request.method, request.path, response.status_code, ms, extra)
        return response


class CurrentUserMiddleware:
    """
    Guarda el usuario autenticado del request en un ContextVar para que
    BaseAuditModel.save() pueda poblarlo automáticamente en created_by / updated_by.

    NOTA: esto NO aplica a QuerySet.update(...), que bypassa save().
    En esos casos, created_by / updated_by deben manejarse explícitamente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            set_current_user(user)
        try:
            return self.get_response(request)
        finally:
            clear_current_user()
