"""
apps/products/presentation/serializers.py
Polymorphic serializers for Product inheritance.
"""
from rest_framework import serializers
from apps.products.domain.models.product import (
    Product, Book, ElectronicsProduct, FashionProduct,
    ProductVariant, ProductImage, Category,
)


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ["id", "name", "slug", "parent", "description", "is_active", "children"]

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ["id", "url", "alt_text", "is_primary", "order"]


class ProductVariantSerializer(serializers.ModelSerializer):
    effective_price = serializers.SerializerMethodField()

    class Meta:
        model  = ProductVariant
        fields = ["id", "name", "sku_suffix", "price_delta", "quantity", "attributes", "is_active", "effective_price"]

    def get_effective_price(self, obj):
        return str(obj.effective_price())


class BaseProductSerializer(serializers.ModelSerializer):
    """Common fields for all product types."""
    images          = ProductImageSerializer(many=True, required=False)
    variants        = ProductVariantSerializer(many=True, read_only=True)
    effective_price = serializers.SerializerMethodField()
    discount_pct    = serializers.SerializerMethodField()
    category_name   = serializers.CharField(source="category.name", read_only=True)
    product_type    = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            "id", "sku", "name", "slug", "description", "category", "category_name",
            "price", "sale_price", "effective_price", "discount_pct", "currency",
            "quantity", "stock_status", "weight", "status",
            "created_at", "updated_at", "images", "variants", "product_type",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at", "stock_status"]

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        product = super().create(validated_data)
        for order, img_data in enumerate(images_data):
            ProductImage.objects.create(product=product, order=order, **img_data)
        return product

    def update(self, instance, validated_data):
        images_data = validated_data.pop("images", None)
        product = super().update(instance, validated_data)
        if images_data is not None:
            instance.images.all().delete()
            for order, img_data in enumerate(images_data):
                ProductImage.objects.create(product=product, order=order, **img_data)
        return product

    def get_effective_price(self, obj):
        return str(obj.effective_price())

    def get_discount_pct(self, obj):
        return obj.discount_percentage()

    def get_product_type(self, obj):
        if hasattr(obj, "book"):
            return "book"
        if hasattr(obj, "electronicsproduct"):
            return "electronics"
        if hasattr(obj, "fashionproduct"):
            return "fashion"
        return "generic"


class BookSerializer(BaseProductSerializer):
    class Meta(BaseProductSerializer.Meta):
        model  = Book
        fields = BaseProductSerializer.Meta.fields + [
            "isbn", "author", "publisher", "published_at", "pages", "language", "genre",
        ]


class ElectronicsSerializer(BaseProductSerializer):
    class Meta(BaseProductSerializer.Meta):
        model  = ElectronicsProduct
        fields = BaseProductSerializer.Meta.fields + [
            "brand", "model_number", "warranty_months", "voltage", "connectivity",
            "os", "processor", "ram_gb", "storage_gb",
        ]


class FashionSerializer(BaseProductSerializer):
    class Meta(BaseProductSerializer.Meta):
        model  = FashionProduct
        fields = BaseProductSerializer.Meta.fields + [
            "brand", "gender", "material", "care_instructions", "season",
        ]


PRODUCT_SERIALIZER_MAP = {
    "book":        BookSerializer,
    "electronics": ElectronicsSerializer,
    "fashion":     FashionSerializer,
}


class PolymorphicProductSerializer(serializers.Serializer):
    """
    Entry-point serializer: picks the right serializer based on 'product_type'.
    Used for creation, detail retrieval, and update.
    """

    def to_representation(self, instance):
        if hasattr(instance, "book"):
            return BookSerializer(instance.book, context=self.context).data
        if hasattr(instance, "electronicsproduct"):
            return ElectronicsSerializer(instance.electronicsproduct, context=self.context).data
        if hasattr(instance, "fashionproduct"):
            return FashionSerializer(instance.fashionproduct, context=self.context).data
        return BaseProductSerializer(instance, context=self.context).data

    def to_internal_value(self, data):
        ptype = data.get("product_type")
        if not ptype and self.instance:
            instance = self.instance
            if isinstance(instance, Book) or hasattr(instance, "book"):
                ptype = "book"
            elif isinstance(instance, ElectronicsProduct) or hasattr(instance, "electronicsproduct"):
                ptype = "electronics"
            elif isinstance(instance, FashionProduct) or hasattr(instance, "fashionproduct"):
                ptype = "fashion"
            else:
                ptype = "generic"
        else:
            ptype = ptype or "generic"

        serializer_class = PRODUCT_SERIALIZER_MAP.get(ptype, BaseProductSerializer)
        serializer = serializer_class(
            instance=self.instance,
            data=data,
            context=self.context,
            partial=getattr(self, "partial", False)
        )
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def create(self, validated_data):
        product_type = self.initial_data.get("product_type", "generic")
        serializer_class = PRODUCT_SERIALIZER_MAP.get(product_type, BaseProductSerializer)
        serializer = serializer_class(context=self.context)
        validated_data["seller_id"] = self.context["request"].user.id
        return serializer.create(validated_data)

    def update(self, instance, validated_data):
        ptype = self.initial_data.get("product_type")
        if not ptype:
            if isinstance(instance, Book) or hasattr(instance, "book"):
                ptype = "book"
            elif isinstance(instance, ElectronicsProduct) or hasattr(instance, "electronicsproduct"):
                ptype = "electronics"
            elif isinstance(instance, FashionProduct) or hasattr(instance, "fashionproduct"):
                ptype = "fashion"
            else:
                ptype = "generic"

        serializer_class = PRODUCT_SERIALIZER_MAP.get(ptype, BaseProductSerializer)
        serializer = serializer_class(context=self.context)
        return serializer.update(instance, validated_data)


class ProductListSerializer(BaseProductSerializer):
    """Lightweight serializer for list views (no heavy nested data)."""
    image_url = serializers.SerializerMethodField()

    class Meta(BaseProductSerializer.Meta):
        fields = [
            "id", "sku", "name", "slug", "category_name", "price", "sale_price",
            "effective_price", "discount_pct", "quantity", "stock_status", "status", "product_type",
            "image_url",
        ]

    def get_image_url(self, obj):
        primary_image = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary_image:
            return primary_image.url
        return None
