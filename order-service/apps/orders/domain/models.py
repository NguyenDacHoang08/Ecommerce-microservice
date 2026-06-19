"""
apps/orders/domain/models.py
Order Aggregate Root with State Machine pattern (DDD).
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class OrderStatus(models.TextChoices):
    PENDING    = "pending",    "Pending"
    CONFIRMED  = "confirmed",  "Confirmed"
    PAID       = "paid",       "Paid"
    PROCESSING = "processing", "Processing"
    SHIPPED    = "shipped",    "Shipped"
    DELIVERED  = "delivered",  "Delivered"
    CANCELLED  = "cancelled",  "Cancelled"
    REFUNDED   = "refunded",   "Refunded"


# Valid state transitions – enforced in domain methods
VALID_TRANSITIONS: dict[str, list[str]] = {
    OrderStatus.PENDING:    [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED:  [OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.PAID:       [OrderStatus.PROCESSING, OrderStatus.REFUNDED],
    OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
    OrderStatus.SHIPPED:    [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED:  [OrderStatus.REFUNDED],
    OrderStatus.CANCELLED:  [],
    OrderStatus.REFUNDED:   [],
}


class Order(models.Model):
    """Order Aggregate Root."""

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=32, unique=True, db_index=True)
    user_id      = models.UUIDField(db_index=True)   # Reference to user-service
    status       = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    # Snapshot of shipping address at order time (denormalised for immutability)
    shipping_name     = models.CharField(max_length=150)
    shipping_phone    = models.CharField(max_length=15)
    shipping_street   = models.CharField(max_length=255)
    shipping_district = models.CharField(max_length=100)
    shipping_city     = models.CharField(max_length=100)
    shipping_country  = models.CharField(max_length=2, default="VN")

    # Pricing
    subtotal         = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    shipping_fee     = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    discount_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    total            = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    currency         = models.CharField(max_length=3, default="VND")

    # References to other services
    payment_id  = models.UUIDField(null=True, blank=True)
    shipment_id = models.UUIDField(null=True, blank=True)

    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        indexes  = [
            models.Index(fields=["user_id", "status"]),
            models.Index(fields=["order_number"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.order_number} [{self.status}]"

    # ── Domain Methods (State Machine) ───────────────────────────────────────

    def _transition_to(self, new_status: str, **kwargs) -> None:
        """
        Enforces valid state transitions.
        Raises ValueError on invalid transition.
        """
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition order from '{self.status}' to '{new_status}'. "
                f"Allowed: {allowed}"
            )
        old_status = self.status
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

        # Append event log
        OrderEvent.objects.create(
            order=self,
            event_type=f"status_changed",
            description=f"{old_status} → {new_status}",
            metadata=kwargs,
        )

    def confirm(self) -> None:
        self._transition_to(OrderStatus.CONFIRMED)

    def mark_paid(self, payment_id: uuid.UUID) -> None:
        self.payment_id = payment_id
        self._transition_to(OrderStatus.PAID, payment_id=str(payment_id))

    def start_processing(self) -> None:
        self._transition_to(OrderStatus.PROCESSING)

    def mark_shipped(self, shipment_id: uuid.UUID, tracking_code: str) -> None:
        self.shipment_id = shipment_id
        self._transition_to(OrderStatus.SHIPPED, shipment_id=str(shipment_id), tracking_code=tracking_code)

    def mark_delivered(self) -> None:
        self._transition_to(OrderStatus.DELIVERED)

    def cancel(self, reason: str = "") -> None:
        self._transition_to(OrderStatus.CANCELLED, reason=reason)

    def refund(self, reason: str = "") -> None:
        self._transition_to(OrderStatus.REFUNDED, reason=reason)

    def calculate_totals(self) -> None:
        """Recalculate subtotal and total from line items."""
        self.subtotal = sum(item.line_total() for item in self.items.all())
        self.total    = self.subtotal + self.shipping_fee - self.discount_amount
        self.save(update_fields=["subtotal", "total", "updated_at"])

    @classmethod
    def generate_order_number(cls) -> str:
        import random, string
        prefix    = timezone.now().strftime("%Y%m%d")
        suffix    = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ORD-{prefix}-{suffix}"


class OrderItem(models.Model):
    """Order Line Item – part of Order aggregate."""

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id   = models.UUIDField()              # Reference to product-service
    product_sku  = models.CharField(max_length=64)
    product_name = models.CharField(max_length=255)  # Snapshot at order time
    variant_id   = models.UUIDField(null=True, blank=True)
    variant_name = models.CharField(max_length=100, blank=True)
    quantity     = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price   = models.DecimalField(max_digits=14, decimal_places=2)  # Snapshot
    currency     = models.CharField(max_length=3, default="VND")

    class Meta:
        db_table = "order_items"

    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

    def __str__(self) -> str:
        return f"{self.quantity}× {self.product_name} @ {self.unit_price}"


class OrderEvent(models.Model):
    """Audit log of all order state changes."""

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    event_type  = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    metadata    = models.JSONField(default=dict, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_events"
        ordering = ["created_at"]
