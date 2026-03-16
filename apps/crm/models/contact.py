from django.conf import settings
from django.db import models
from common.models import BaseAuditModel


class ContactType(models.TextChoices):
    OWNER = "owner", "Owner"
    INTERESTED = "interested", "Interested"
    OTHER = "other", "Other"

class DocumentType(models.TextChoices):
    DNI = "dni", "DNI"
    PASSPORT = "passport", "Passport"
    CE = "ce", "Carnet de extranjería"

class Gender(models.TextChoices):
    M = "M", "Masculino"
    F = "F", "Femenino"
    OT = "O", "Otro"

class Contact(BaseAuditModel):
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_contacts",
    )

    full_name = models.CharField(max_length=255)
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        null=True,
        blank=True,
    )
    document_number = models.CharField(max_length=50, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    photo = models.ImageField(upload_to="contacts/photos/", null=True, blank=True)
    contact_type = models.CharField(max_length=30, choices=ContactType.choices, default=ContactType.OTHER)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "contact"
        ordering = ["full_name"]

    def __str__(self) -> str:
        return self.full_name