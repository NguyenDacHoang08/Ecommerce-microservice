"""
apps/payments/domain/models.py
Payment Aggregate – supports Stripe and VNPay gateways.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from django.db import models


class PaymentStatus(models.TextChoices):
    PENDING   = "pending",   "Pending"
    INITIATED = "initiated", "Initiated"
    SUCCESS   = "success",   "Success"
    FAILED    = "failed",    "Failed"
    REFUNDED  = "refunded",  "Refunded"
    CANCELLED = "cancelled", "Cancelled"


class PaymentGateway(models.TextChoices):
    STRIPE  = "stripe",  "Stripe"
    VNPAY   = "vnpay",   "VNPay"
    COD     = "cod",     "Cash on Delivery"
    MOMO    = "momo",    "MoMo"
    ZALOPAY = "zalopay", "ZaloPay"


class Payment(models.Model):
    """Payment Aggregate Root."""

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id     = models.UUIDField(db_index=True, unique=True)
    user_id      = models.UUIDField(db_index=True)
    gateway      = models.CharField(max_length=20, choices=PaymentGateway.choices)
    status       = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    amount       = models.DecimalField(max_digits=14, decimal_places=2)
    currency     = models.CharField(max_length=3, default="VND")

    # Gateway-specific identifiers
    gateway_payment_id   = models.CharField(max_length=255, blank=True, db_index=True)
    gateway_txn_id       = models.CharField(max_length=255, blank=True)
    gateway_response     = models.JSONField(default=dict, blank=True)

    # URLs
    checkout_url   = models.URLField(max_length=2048, blank=True)
    return_url     = models.URLField(max_length=2048, blank=True)
    webhook_secret = models.CharField(max_length=255, blank=True)

    paid_at    = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        indexes  = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["user_id", "status"]),
        ]

    def __str__(self) -> str:
        return f"Payment {self.id} [{self.gateway}] {self.status}"

    # ── Domain Methods ───────────────────────────────────────────────────────

    def mark_success(self, txn_id: str, gateway_response: dict) -> None:
        from django.utils import timezone
        if self.status == PaymentStatus.SUCCESS:
            raise ValueError("Payment already marked as success.")
        self.status           = PaymentStatus.SUCCESS
        self.gateway_txn_id   = txn_id
        self.gateway_response = gateway_response
        self.paid_at          = timezone.now()
        self.save(update_fields=["status", "gateway_txn_id", "gateway_response", "paid_at", "updated_at"])

    def mark_failed(self, reason: str, gateway_response: dict | None = None) -> None:
        self.status           = PaymentStatus.FAILED
        self.gateway_response = gateway_response or {"reason": reason}
        self.save(update_fields=["status", "gateway_response", "updated_at"])

    def initiate_refund(self) -> "Refund":
        if self.status != PaymentStatus.SUCCESS:
            raise ValueError("Can only refund successful payments.")
        return Refund.objects.create(
            payment=self,
            amount=self.amount,
            currency=self.currency,
        )

    def is_paid(self) -> bool:
        return self.status == PaymentStatus.SUCCESS


class Refund(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment      = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    amount       = models.DecimalField(max_digits=14, decimal_places=2)
    currency     = models.CharField(max_length=3, default="VND")
    reason       = models.TextField(blank=True)
    gateway_refund_id = models.CharField(max_length=255, blank=True)
    status       = models.CharField(max_length=20, default="pending")
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_refunds"
