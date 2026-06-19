"""
apps/cart/serializers.py
DRF Serializers for Cart and CartItem
"""
from rest_framework import serializers
from .models import Cart, CartItem

class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product_id", "quantity", "added_at", "updated_at", "product"]
        read_only_fields = ["id", "added_at", "updated_at"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def get_product(self, obj):
        import requests
        from django.conf import settings
        import logging
        logger = logging.getLogger(__name__)

        try:
            service_url = getattr(settings, "PRODUCT_SERVICE_URL", "http://product-service:8001")
            url = f"{service_url}/api/products/{obj.product_id}/"
            response = requests.get(url, timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                images = data.get("images", [])
                primary_image = next((img for img in images if img.get("is_primary")), None) or (images[0] if images else None)
                image_url = primary_image.get("url") if primary_image else None
                return {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "price": data.get("price"),
                    "status": data.get("status"),
                    "category": data.get("category_name"),
                    "image_url": image_url,
                    "images": images,
                }
            else:
                logger.warning(f"Failed to fetch product details for ID: {obj.product_id}. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching product details for ID: {obj.product_id}. Exception: {e}")
        return None

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cart
        fields = ["id", "user_id", "items", "created_at", "updated_at"]
        read_only_fields = ["id", "user_id", "created_at", "updated_at"]

class AddItemSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=255)
    quantity   = serializers.IntegerField(default=1, min_value=1)

class UpdateItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
