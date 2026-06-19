"""
apps/orders/models.py
Order Domain Models
"""
import uuid
from django.db import models

class OrderStatus(models.TextChoices):
    PROCESSING = "PROCESSING", "Processing"
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"
    DELIVERED = "DELIVERED", "Delivered"

class Order(models.Model):
    """
    Order aggregate root.
    Links to a user_id from the user-service.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id     = models.CharField(max_length=255, db_index=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status      = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PROCESSING)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} (User: {self.user_id})"

    def calculate_total(self):
        """Domain logic to calculate total price from items"""
        total = sum((item.price * item.quantity) for item in self.items.all())
        self.total_price = total
        self.save()

class OrderItem(models.Model):
    """
    Item within an order.
    Links to a product_id from the product-service.
    Prices are frozen at the time of order creation.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order      = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_id = models.CharField(max_length=255, db_index=True)
    quantity   = models.PositiveIntegerField(default=1)
    price      = models.DecimalField(max_digits=12, decimal_places=2, help_text="Price per unit at time of order")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_items"
        ordering = ["created_at"]

    def __str__(self):
        return f"OrderItem {self.product_id} (x{self.quantity}) in {self.order.id}"
