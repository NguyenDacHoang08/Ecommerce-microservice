"""
apps/shipments/domain/models.py
Shipment Aggregate.
"""
from __future__ import annotations

import uuid
from django.db import models


class ShipmentStatus(models.TextChoices):
    PENDING     = "pending",     "Pending"
    PICKED_UP   = "picked_up",  "Picked Up"
    IN_TRANSIT  = "in_transit",  "In Transit"
    OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
    DELIVERED   = "delivered",   "Delivered"
    FAILED      = "failed",      "Failed Delivery"
    RETURNED    = "returned",    "Returned"


class Carrier(models.TextChoices):
    GIAO_HANG_NHANH = "ghn",  "Giao Hàng Nhanh"
    GIAO_HANG_TIET_KIEM = "ghtk", "Giao Hàng Tiết Kiệm"
    VNPOST  = "vnpost",  "VNPost"
    DHL     = "dhl",     "DHL"
    FEDEX   = "fedex",   "FedEx"


class Shipment(models.Model):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id       = models.UUIDField(unique=True, db_index=True)
    carrier        = models.CharField(max_length=20, choices=Carrier.choices)
    tracking_code  = models.CharField(max_length=100, unique=True, blank=True)
    status         = models.CharField(max_length=30, choices=ShipmentStatus.choices, default=ShipmentStatus.PENDING)

    # Sender
    sender_name    = models.CharField(max_length=150)
    sender_phone   = models.CharField(max_length=15)
    sender_address = models.TextField()

    # Recipient
    recipient_name    = models.CharField(max_length=150)
    recipient_phone   = models.CharField(max_length=15)
    recipient_address = models.TextField()
    recipient_city    = models.CharField(max_length=100)

    weight_kg         = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    shipping_fee      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cod_amount        = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Cash on Delivery")

    estimated_delivery = models.DateField(null=True, blank=True)
    delivered_at       = models.DateTimeField(null=True, blank=True)
    carrier_response   = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shipments"

    def __str__(self) -> str:
        return f"Shipment {self.tracking_code} [{self.status}]"

    def update_status(self, new_status: str, note: str = "") -> None:
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])
        TrackingEvent.objects.create(shipment=self, status=new_status, note=note)

    def mark_delivered(self) -> None:
        from django.utils import timezone
        self.delivered_at = timezone.now()
        self.update_status(ShipmentStatus.DELIVERED, "Package delivered successfully")


class TrackingEvent(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment   = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="events")
    status     = models.CharField(max_length=30)
    location   = models.CharField(max_length=200, blank=True)
    note       = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shipment_tracking_events"
        ordering = ["-created_at"]
