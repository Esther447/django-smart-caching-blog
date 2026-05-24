from django.db import models
from merchants.models import Merchant

class FinancingRequest(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField()
    status = models.CharField(max_length=50, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FinancingRequest #{self.id} - {self.merchant.name}"
