from django.conf import settings
from django.db import models
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField


class BaseAuditModel(models.Model):
    created_at = CreationDateTimeField(db_index=True)
    updated_at = ModificationDateTimeField(db_index=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",)

    class Meta:
        abstract = True


class BaseDefinitionModel(models.Model):
    """
    Para catálogos: name + is_active.
    """
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name


class BaseModel(BaseAuditModel, BaseDefinitionModel):
    """
    Base final para catálogos (Audit + Definition).
    """
    class Meta:
        abstract = True