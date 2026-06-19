"""
apps/carts/domain/models.py
Cart Aggregate – PostgreSQL-backed, Redis cached.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class Cart(models.Model):

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id    = models.UUIDField(null=True, blank=True, db_index=True)   # null = guest cart
    session_id = models.CharField(max_length=64, db_index=True, blank=True)
    currency   = models.CharField(max_length=3, default="VND")
    coupon_code   = models.CharField(max_length=50, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts"
        indexes  = [models.Index(fields=["user_id", "is_active"])]

    def __str__(self) -> str:
        owner = f"user:{self.user_id}" if self.user_id else f"session:{self.session_id}"
        return f"Cart({owner})"

    # ── Domain Methods ───────────────────────────────────────────────────────

    def add_item(self, product_id: uuid.UUID, quantity: int, unit_price: Decimal,
                 product_name: str, sku: str, variant_id: uuid.UUID | None = None) -> CartItem:
        """Domain action: add or update item in cart."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        item, created = self.items.get_or_create(
            product_id=product_id,
            variant_id=variant_id,
            defaults={
                "quantity":     quantity,
                "unit_price":   unit_price,
                "product_name": product_name,
                "sku":          sku,
            }
        )
        if not created:
            item.quantity += quantity
            item.unit_price = unit_price  # Refresh price
            item.save(update_fields=["quantity", "unit_price"])

        self.save(update_fields=["updated_at"])
        return item

    def remove_item(self, product_id: uuid.UUID, variant_id: uuid.UUID | None = None) -> None:
        self.items.filter(product_id=product_id, variant_id=variant_id).delete()
        self.save(update_fields=["updated_at"])

    def update_item_quantity(self, product_id: uuid.UUID, quantity: int,
                             variant_id: uuid.UUID | None = None) -> None:
        if quantity <= 0:
            self.remove_item(product_id, variant_id)
            return
        self.items.filter(product_id=product_id, variant_id=variant_id).update(quantity=quantity)
        self.save(update_fields=["updated_at"])

    def clear(self) -> None:
        self.items.all().delete()
        self.discount_amount = Decimal("0")
        self.coupon_code     = ""
        self.save(update_fields=["discount_amount", "coupon_code", "updated_at"])

    def subtotal(self) -> Decimal:
        return sum(item.line_total() for item in self.items.all())

    def total(self) -> Decimal:
        return max(self.subtotal() - self.discount_amount, Decimal("0"))

    def item_count(self) -> int:
        return self.items.aggregate(total=models.Sum("quantity"))["total"] or 0

    def is_empty(self) -> bool:
        return not self.items.exists()

    def apply_coupon(self, code: str, discount: Decimal) -> None:
        """Business rule: coupon discount cannot exceed subtotal."""
        discount = min(discount, self.subtotal())
        self.coupon_code     = code
        self.discount_amount = discount
        self.save(update_fields=["coupon_code", "discount_amount", "updated_at"])

    def merge_guest_cart(self, guest_cart: "Cart") -> None:
        """Domain action: merge anonymous cart into authenticated user's cart."""
        for guest_item in guest_cart.items.all():
            self.add_item(
                product_id=guest_item.product_id,
                quantity=guest_item.quantity,
                unit_price=guest_item.unit_price,
                product_name=guest_item.product_name,
                sku=guest_item.sku,
                variant_id=guest_item.variant_id,
            )
        guest_cart.delete()


class CartItem(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart         = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product_id   = models.UUIDField()
    variant_id   = models.UUIDField(null=True, blank=True)
    sku          = models.CharField(max_length=64)
    product_name = models.CharField(max_length=255)
    quantity     = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price   = models.DecimalField(max_digits=14, decimal_places=2)
    added_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "cart_items"
        unique_together = [("cart", "product_id", "variant_id")]

    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity
