"""
apps/shipping/models.py
Shipping Domain Models
"""
import uuid
import random
import string
from django.db import models
from django.utils import timezone
from datetime import timedelta

class ShippingStatus(models.TextChoices):
    PROCESSING = "PROCESSING", "Processing"
    SHIPPING   = "SHIPPING", "Shipping"
    DELIVERED  = "DELIVERED", "Delivered"

def generate_tracking_number():
    """Generate a random tracking number (e.g., VN-A1B2C3D4)"""
    chars = string.ascii_uppercase + string.digits
    random_str = ''.join(random.choices(chars, k=8))
    return f"VN-{random_str}"

def default_estimated_delivery():
    """Default delivery is 3 days from now"""
    return timezone.now() + timedelta(days=3)

class Shipment(models.Model):
    """
    Shipment aggregate root.
    Links to an order_id from the order-service.
    """
    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id           = models.CharField(max_length=255, unique=True, db_index=True)
    user_id            = models.CharField(max_length=255, db_index=True)
    address            = models.TextField(help_text="Full shipping address details")
    status             = models.CharField(max_length=20, choices=ShippingStatus.choices, default=ShippingStatus.PROCESSING)
    tracking_number    = models.CharField(max_length=50, unique=True, default=generate_tracking_number)
    estimated_delivery = models.DateTimeField(default=default_estimated_delivery)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shipments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Shipment {self.tracking_number} for Order {self.order_id}"

    def update_status(self, new_status):
        self.status = new_status
        self.save()
