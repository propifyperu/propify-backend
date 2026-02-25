from django.db import models
from common.models import BaseAuditModel
from apps.locations.models import Country, Department
from django.conf import settings

class UserProfile(BaseAuditModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile",)

    avatar_url = models.FileField(max_length=500, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    nro_document = models.CharField(max_length=30, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_profiles",)
    city = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_profiles",)

    class Meta:
        db_table = "user_profile"

    def __str__(self) -> str:
        return f"Profile - {self.user_id}"