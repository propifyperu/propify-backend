from django.db import models
from common.models import BaseModel


class Country(BaseModel):
    code = models.CharField(max_length=3, unique=True)  # PER, USA, etc.

    class Meta:
        db_table = "country"
        ordering = ["name"]