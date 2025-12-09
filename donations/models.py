from django.db import models

class Donation(models.Model):
    donor_name = models.CharField(max_length=100, blank=True)
    amount_sats = models.IntegerField()
    invoice = models.TextField()
    payment_hash = models.CharField(max_length=200, unique=True)
    status = models.CharField(max_length=20, default="PENDING")
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor_name} - {self.amount_sats} sats - {self.status}"
