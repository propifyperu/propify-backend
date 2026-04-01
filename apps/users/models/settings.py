from django.db import models
from common.models import BaseAuditModel
from django.conf import settings

class ThemeChoices(models.TextChoices):
    LIGHT = "light", "Light"
    MIXED = "mixed", "Mixed"
    DARK = "dark", "Dark"

class UserSettings(BaseAuditModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="settings",)
    privacy_enabled = models.BooleanField(default=True)
    notifications_enabled = models.BooleanField(default=True)
    whatsapp_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    device_enabled = models.BooleanField(default=True)
    theme = models.CharField(max_length=50,choices=ThemeChoices.choices, default=ThemeChoices.LIGHT)
    language = models.CharField(max_length=30, blank=True, null=True)
    timezone = models.CharField(max_length=64, blank=True, null=True)
    
    class Meta:
        db_table = "user_settings"

    def __str__(self) -> str:
        return f"Settings - {self.user_id}"