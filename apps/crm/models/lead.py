from django.conf import settings
from django.db import models
from common.models import BaseAuditModel

class UserLastMessage(models.TextChoices):
    BOT = "bot", "Bot"
    AGENT = "agent", "Agent"
    LEAD = "lead", "Lead"

class Lead(BaseAuditModel):  #EntradaLead
    contact = models.ForeignKey(
        "crm.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_leads",
    )
    area = models.ForeignKey(
        "users.Area",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )
    lead_status = models.ForeignKey(
        "catalogs.LeadStatus",
        on_delete=models.PROTECT,
        related_name="leads",
    )
    canal_lead = models.ForeignKey(
        "catalogs.CanalLead",
        on_delete=models.PROTECT,
        related_name="leads",
    )
    operation_types = models.ManyToManyField(
        "catalogs.OperationType",
        related_name="leads",
        blank=True
    )
        # Relación directa a propiedades (MVP)
    properties = models.ManyToManyField(
        "properties.Property",
        related_name="leads",
        blank=True,
    )

    source_detail = models.CharField(max_length=255, null=True, blank=True) #para poner deatalle del canal / puede ser una campaña.... 
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Chat/WhatsApp/Chatwoot (si lo usarás)
    date_entry = models.DateTimeField(null=True, blank=True)
    id_chatwoot = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    date_last_message = models.DateTimeField(null=True, blank=True)
    user_last_message = models.CharField(
        max_length=10,
        choices=UserLastMessage.choices,
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "lead"
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"Lead {self.id} - {self.full_name}"