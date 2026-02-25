from common.models import BaseModel


class Area(BaseModel):
    class Meta:
        db_table = "area"
        ordering = ["name"]