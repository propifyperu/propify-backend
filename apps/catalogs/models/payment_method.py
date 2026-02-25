from common.models import BaseModel

class PaymentMethod(BaseModel):
    class Meta:
        db_table = "payment_method"
        ordering = ["name"]