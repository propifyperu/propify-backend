from common.models import BaseModel

class LeadStatus(BaseModel):
    class Meta:
        db_table = "lead_status"
        ordering = ["name"]