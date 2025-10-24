from django.conf import settings
from django.db import models

class Payment(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
    ]
    PROVIDERS = [
        ("paynow", "Paynow"),
        ("stripe", "Stripe"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    currency = models.CharField(max_length=10, default="usd")
    status = models.CharField(max_length=20, choices=STATUS, default="pending", db_index=True)
    provider = models.CharField(max_length=20, choices=PROVIDERS, default="paynow", db_index=True)

    # Paynow fields
    poll_url = models.URLField(blank=True, null=True)
    provider_reference = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    provider_status = models.CharField(max_length=50, blank=True, null=True)

    # Stripe fields (kept nullable, safe to ignore if not using Stripe)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} -> {self.course} {self.amount} {self.currency} [{self.status}]"