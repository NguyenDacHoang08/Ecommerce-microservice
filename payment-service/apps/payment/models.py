"""
apps/payment/models.py
Payment Domain Models
"""
import uuid
from django.db import models

class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED  = "FAILED", "Failed"

class PaymentMethod(models.TextChoices):
    CREDIT_CARD = "CREDIT_CARD", "Credit Card"
    PAYPAL      = "PAYPAL", "PayPal"
    BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
    COD         = "COD", "Cash on Delivery"

class Payment(models.Model):
    """
    Payment aggregate root.
    Links to an order_id from the order-service.
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id       = models.CharField(max_length=255, db_index=True)
    user_id        = models.CharField(max_length=255, db_index=True)
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    status         = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_method = models.CharField(max_length=50, choices=PaymentMethod.choices, default=PaymentMethod.CREDIT_CARD)
    transaction_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID from external payment gateway")
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.id} for Order {self.order_id} ({self.status})"

    def mark_as_success(self, transaction_id=None):
        self.status = PaymentStatus.SUCCESS
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()

    def mark_as_failed(self):
        self.status = PaymentStatus.FAILED
        self.save()
