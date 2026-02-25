from django.contrib.auth.models import AbstractUser
from django.db import models
from .role import Role


class User(AbstractUser):
    """ 
    (AbstractUser).
    Mantiene username/first_name/last_name/email/password de Django.
    """

    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True, related_name="users",)
    external_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "user"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.get_full_name() or self.username