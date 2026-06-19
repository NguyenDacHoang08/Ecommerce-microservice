"""
apps/orders/serializers.py
DRF Serializers for Order and OrderItem
"""
from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "quantity", "price", "created_at"]
        read_only_fields = ["id", "price", "created_at"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ["id", "user_id", "total_price", "status", "items", "created_at", "updated_at"]
        read_only_fields = ["id", "user_id", "total_price", "created_at", "updated_at"]

class CreateOrderSerializer(serializers.Serializer):
    # Depending on implementation, you might accept cart_id from client 
    # but since cart belongs to user, we can just fetch the user's cart.
    pass # No fields needed, creating from user's cart
