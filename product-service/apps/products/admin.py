"""
apps/products/admin.py
Django Admin registration for the Product domain.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.products.domain.models.product import (
    Category, Product, Book, ElectronicsProduct, FashionProduct,
    ProductVariant, ProductImage,
)


# ── Inlines ───────────────────────────────────────────────────────────────────

class ProductImageInline(admin.TabularInline):
    model  = ProductImage
    extra  = 1
    fields = ["url", "alt_text", "is_primary", "order"]

    def image_preview(self, obj):
        if obj.url:
            return format_html('<img src="{}" style="height:50px;"/>', obj.url)
        return "-"
    image_preview.short_description = "Preview"


class ProductVariantInline(admin.TabularInline):
    model  = ProductVariant
    extra  = 1
    fields = ["name", "sku_suffix", "price_delta", "quantity", "attributes", "is_active"]


# ── Category Admin ────────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display   = ["name", "slug", "parent", "is_active", "created_at"]
    list_filter    = ["is_active"]
    search_fields  = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    ordering       = ["name"]


# ── Base Product Admin ────────────────────────────────────────────────────────

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display   = [
        "sku", "name", "category", "price_display", "sale_price",
        "quantity", "stock_status", "status", "created_at"
    ]
    list_filter    = ["status", "stock_status", "category", "currency"]
    search_fields  = ["name", "sku", "slug"]
    readonly_fields = ["id", "slug", "stock_status", "created_at", "updated_at"]
    ordering       = ["-created_at"]
    inlines        = [ProductImageInline, ProductVariantInline]

    fieldsets = (
        ("Identity", {
            "fields": ("id", "sku", "name", "slug", "description", "category", "seller_id"),
        }),
        ("Pricing", {
            "fields": ("price", "sale_price", "cost_price", "currency"),
        }),
        ("Inventory", {
            "fields": ("quantity", "low_stock_threshold", "stock_status"),
        }),
        ("Physical", {
            "fields": ("weight", "length", "width", "height"),
            "classes": ("collapse",),
        }),
        ("Status & Dates", {
            "fields": ("status", "created_at", "updated_at"),
        }),
    )

    def price_display(self, obj):
        effective = obj.effective_price()
        if obj.sale_price and obj.sale_price < obj.price:
            return format_html(
                '<span style="color:red;">{}</span> <s style="color:grey;">{}</s>',
                effective, obj.price
            )
        return effective
    price_display.short_description = "Price"

    actions = ["publish_products", "deactivate_products"]

    @admin.action(description="✅ Publish selected products")
    def publish_products(self, request, queryset):
        published, failed = 0, 0
        for product in queryset:
            try:
                product.publish()
                published += 1
            except ValueError:
                failed += 1
        self.message_user(
            request,
            f"Published: {published}, Failed: {failed}",
        )

    @admin.action(description="🚫 Deactivate selected products")
    def deactivate_products(self, request, queryset):
        count = queryset.update(status="inactive")
        self.message_user(request, f"Deactivated {count} product(s).")


# ── Specialised Product Admins ────────────────────────────────────────────────

@admin.register(Book)
class BookAdmin(ProductAdmin):
    list_display = ProductAdmin.list_display + ["isbn", "author", "language"]
    search_fields = ProductAdmin.search_fields + ["isbn", "author", "publisher"]

    fieldsets = ProductAdmin.fieldsets + (
        ("Book Details", {
            "fields": ("isbn", "author", "publisher", "published_at", "pages", "language", "genre"),
        }),
    )


@admin.register(ElectronicsProduct)
class ElectronicsAdmin(ProductAdmin):
    list_display = ProductAdmin.list_display + ["brand", "warranty_months"]
    search_fields = ProductAdmin.search_fields + ["brand", "model_number"]
    list_filter  = ProductAdmin.list_filter + ["brand", "os"]  # type: ignore[operator]

    fieldsets = ProductAdmin.fieldsets + (
        ("Electronics Details", {
            "fields": ("brand", "model_number", "warranty_months", "voltage",
                       "connectivity", "os", "processor", "ram_gb", "storage_gb"),
        }),
    )


@admin.register(FashionProduct)
class FashionAdmin(ProductAdmin):
    list_display = ProductAdmin.list_display + ["brand", "gender", "season"]
    search_fields = ProductAdmin.search_fields + ["brand", "material"]
    list_filter  = ProductAdmin.list_filter + ["gender", "season"]  # type: ignore[operator]

    fieldsets = ProductAdmin.fieldsets + (
        ("Fashion Details", {
            "fields": ("brand", "gender", "material", "care_instructions", "season"),
        }),
    )


# ── Variant & Image Admin ─────────────────────────────────────────────────────

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display  = ["name", "product", "sku_suffix", "price_delta", "quantity", "is_active"]
    list_filter   = ["is_active"]
    search_fields = ["name", "product__name", "product__sku"]
    readonly_fields = ["id"]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display  = ["product", "url", "alt_text", "is_primary", "order"]
    list_filter   = ["is_primary"]
    search_fields = ["product__name", "alt_text"]
    readonly_fields = ["id"]
