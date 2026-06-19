"""
apps/products/domain/models/product.py
Rich Domain Model – Product aggregate with multi-table inheritance (DDD).

Hierarchy:
    BaseProduct (abstract value objects + invariants)
    └── Product (concrete aggregate root)
        ├── Book
        ├── ElectronicsProduct
        └── FashionProduct
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.utils import timezone


class ProductStatus(models.TextChoices):
    DRAFT     = "draft",     "Draft"
    ACTIVE    = "active",    "Active"
    INACTIVE  = "inactive",  "Inactive"
    DELETED   = "deleted",   "Deleted"


class StockStatus(models.TextChoices):
    IN_STOCK     = "in_stock",     "In Stock"
    LOW_STOCK    = "low_stock",    "Low Stock"
    OUT_OF_STOCK = "out_of_stock", "Out of Stock"
    DISCONTINUED = "discontinued", "Discontinued"


class Category(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(max_length=120, unique=True)
    parent      = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = "product_categories"
        verbose_name_plural = "categories"
        ordering  = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Product Aggregate Root.
    Business invariants enforced via domain methods.
    Uses multi-table inheritance for specialisation.
    """

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku         = models.CharField(max_length=64, unique=True, db_index=True)
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(max_length=280, unique=True)
    description = models.TextField(blank=True)
    category    = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    seller_id   = models.UUIDField(db_index=True)   # FK to user-service (no hard FK across services)

    # Pricing Value Object (embedded)
    price         = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    sale_price    = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    cost_price    = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency      = models.CharField(max_length=3, default="VND")

    # Inventory Value Object
    quantity     = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    stock_status = models.CharField(max_length=20, choices=StockStatus.choices, default=StockStatus.OUT_OF_STOCK)

    # Physical attributes
    weight       = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, help_text="kg")
    length       = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="cm")
    width        = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="cm")
    height       = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="cm")

    status     = models.CharField(max_length=20, choices=ProductStatus.choices, default=ProductStatus.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        indexes  = [
            models.Index(fields=["sku"]),
            models.Index(fields=["status", "category"]),
            models.Index(fields=["seller_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.sku}] {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self._update_stock_status()
        super().save(*args, **kwargs)

    # ── Domain Methods ───────────────────────────────────────────────────────

    def _update_stock_status(self) -> None:
        """Invariant: keep stock_status in sync with quantity."""
        if self.quantity == 0:
            self.stock_status = StockStatus.OUT_OF_STOCK
        elif self.quantity <= self.low_stock_threshold:
            self.stock_status = StockStatus.LOW_STOCK
        else:
            self.stock_status = StockStatus.IN_STOCK

    def effective_price(self) -> Decimal:
        """Return sale price if active, otherwise regular price."""
        if self.sale_price and self.sale_price < self.price:
            return self.sale_price
        return self.price

    def discount_percentage(self) -> int:
        if self.sale_price and self.sale_price < self.price:
            return int((1 - self.sale_price / self.price) * 100)
        return 0

    def reserve_stock(self, qty: int) -> None:
        """Domain action: reserve stock for an order."""
        if qty <= 0:
            raise ValueError("Quantity must be positive.")
        if self.quantity < qty:
            raise ValueError(f"Insufficient stock. Available: {self.quantity}, Requested: {qty}")
        self.quantity -= qty
        self._update_stock_status()
        self.save(update_fields=["quantity", "stock_status", "updated_at"])

    def release_stock(self, qty: int) -> None:
        """Domain action: release reserved stock (order cancelled)."""
        if qty <= 0:
            raise ValueError("Quantity must be positive.")
        self.quantity += qty
        self._update_stock_status()
        self.save(update_fields=["quantity", "stock_status", "updated_at"])

    def publish(self) -> None:
        """Domain action: publish a draft product."""
        if self.status == ProductStatus.ACTIVE:
            raise ValueError("Product is already active.")
        if not self.name or not self.price:
            raise ValueError("Cannot publish: name and price are required.")
        self.status = ProductStatus.ACTIVE
        self.save(update_fields=["status", "updated_at"])

    def is_available(self) -> bool:
        return self.status == ProductStatus.ACTIVE and self.stock_status != StockStatus.OUT_OF_STOCK


# ── Specialised Product Types (Multi-Table Inheritance) ─────────────────────

class Book(Product):
    """Specialisation: Book – extra domain attributes."""
    isbn        = models.CharField(max_length=13, unique=True, db_index=True)
    author      = models.CharField(max_length=255)
    publisher   = models.CharField(max_length=255, blank=True)
    published_at = models.DateField(null=True, blank=True)
    pages       = models.PositiveIntegerField(null=True, blank=True)
    language    = models.CharField(max_length=10, default="vi")
    genre       = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "products_books"

    def is_translated(self) -> bool:
        return self.language != "vi"


class ElectronicsProduct(Product):
    """Specialisation: Electronics."""
    brand         = models.CharField(max_length=100)
    model_number  = models.CharField(max_length=100, blank=True)
    warranty_months = models.PositiveIntegerField(default=12)
    voltage       = models.CharField(max_length=20, blank=True, help_text="e.g. 220V")
    connectivity  = models.JSONField(default=list, blank=True, help_text='["WiFi", "Bluetooth"]')
    os            = models.CharField(max_length=100, blank=True)
    processor     = models.CharField(max_length=200, blank=True)
    ram_gb        = models.PositiveIntegerField(null=True, blank=True)
    storage_gb    = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "products_electronics"

    def is_under_warranty(self, purchase_date) -> bool:
        from dateutil.relativedelta import relativedelta
        return purchase_date + relativedelta(months=self.warranty_months) > timezone.now().date()


class FashionProduct(Product):
    """Specialisation: Fashion (clothing, shoes, accessories)."""

    class Gender(models.TextChoices):
        MALE    = "male",    "Male"
        FEMALE  = "female",  "Female"
        UNISEX  = "unisex",  "Unisex"
        KIDS    = "kids",    "Kids"

    brand    = models.CharField(max_length=100, blank=True)
    gender   = models.CharField(max_length=10, choices=Gender.choices, default=Gender.UNISEX)
    material = models.CharField(max_length=200, blank=True)
    care_instructions = models.TextField(blank=True)
    season   = models.CharField(max_length=50, blank=True, help_text="Spring, Summer, etc.")

    class Meta:
        db_table = "products_fashion"


class ProductVariant(models.Model):
    """
    Product variants: size M / color Red / etc.
    Belongs to FashionProduct or ElectronicsProduct.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name       = models.CharField(max_length=100, help_text="e.g. 'Size M - Red'")
    sku_suffix = models.CharField(max_length=20)
    price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    quantity   = models.PositiveIntegerField(default=0)
    attributes = models.JSONField(default=dict, help_text='{"size": "M", "color": "red"}')
    is_active  = models.BooleanField(default=True)

    class Meta:
        db_table = "product_variants"
        unique_together = [("product", "sku_suffix")]

    def effective_price(self) -> Decimal:
        return self.product.effective_price() + self.price_delta


class ProductImage(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    url        = models.URLField(max_length=500)
    alt_text   = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "product_images"
        ordering = ["order"]
