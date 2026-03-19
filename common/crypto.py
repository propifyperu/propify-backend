# apps/common/crypto.py
from __future__ import annotations

from django.conf import settings

try:
    from cryptography.fernet import Fernet
except Exception as e:
    Fernet = None


def decrypt_value(value: str | None) -> str | None:
    """
    Desencripta strings Fernet típicos que vienen como 'gAAAAA...'
    Usa settings.FIELD_ENCRYPTION_KEY (o ENCRYPTION_KEY).
    """
    if value is None:
        return None

    s = str(value)

    # si no parece Fernet, devuélvelo tal cual
    if not s.startswith("gAAAAA"):
        return s

    if Fernet is None:
        # cryptography no está instalado
        return s

    key = getattr(settings, "FIELD_ENCRYPTION_KEY", None) or getattr(settings, "ENCRYPTION_KEY", None)
    if not key:
        return s

    try:
        f = Fernet(key)
        return f.decrypt(s.encode("utf-8")).decode("utf-8")
    except Exception:
        # si no matchea la key, o está corrupto, etc.
        return s