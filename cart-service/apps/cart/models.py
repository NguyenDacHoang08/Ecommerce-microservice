"""
apps/cart/models.py
Cart Domain Models
"""
import uuid
from django.db import models

class Cart(models.Model):
    """
    Cart aggregate root.
    Links to a user_id from the user-service.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id    = models.CharField(max_length=255, unique=True, db_index=True) # UUID string or similar
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cart for user: {self.user_id}"

    def clear(self):
        """Domain logic to clear all items in the cart"""
        self.items.all().delete()
        self.save() # update the updated_at timestamp

class CartItem(models.Model):
    """
    Item within a cart.
    Links to a product_id from the product-service.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart       = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product_id = models.CharField(max_length=255, db_index=True)
    quantity   = models.PositiveIntegerField(default=1)
    added_at   = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_items"
        unique_together = ("cart", "product_id") # A product should only appear once per cart
        ordering = ["added_at"]

    def __str__(self):
        return f"CartItem {self.product_id} (x{self.quantity}) in {self.cart.id}"

    def update_quantity(self, quantity):
        """Domain logic to update quantity"""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        self.quantity = quantity
        self.save()
