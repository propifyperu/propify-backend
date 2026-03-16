from django.db import models
from common.models import BaseAuditModel


class ExchangeRate(BaseAuditModel):
    base_currency = models.ForeignKey("catalogs.Currency", on_delete=models.PROTECT, related_name="base_rates")
    quote_currency = models.ForeignKey("catalogs.Currency", on_delete=models.PROTECT, related_name="quote_rates")

    rate = models.DecimalField(max_digits=12, decimal_places=6)
    rate_date = models.DateTimeField(db_index=True)
    provider = models.CharField(max_length=120, blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "exchange_rate"
        constraints = [
            models.UniqueConstraint(fields=["base_currency", "quote_currency", "rate_date"], name="uq_exchange_rate_pair_date"),
        ]