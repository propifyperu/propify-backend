from common.models import BaseModel

class CanalLead(BaseModel):
    class Meta:
        db_table = "canal_lead"
        ordering = ["name"]