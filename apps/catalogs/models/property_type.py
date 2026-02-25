from common.models import BaseModel


class PropertyType(BaseModel):
    class Meta:
        db_table = "property_type"
        ordering = ["name"]