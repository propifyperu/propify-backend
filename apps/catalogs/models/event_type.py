from common.models import BaseModel

class EventType(BaseModel):
    class Meta:
        db_table = "event_type"
        ordering = ["name"]