from common.models import BaseModel

class PropertyStatus(BaseModel):
    class Meta:
        db_table = "property_status"
        ordering = ["name"]