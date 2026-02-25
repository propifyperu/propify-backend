from common.models import BaseModel


class OperationType(BaseModel):
    class Meta:
        db_table = "operation_type"
        ordering = ["name"]