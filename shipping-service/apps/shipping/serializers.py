"""
apps/shipping/serializers.py
DRF Serializers for Shipping
"""
from rest_framework import serializers
from .models import Shipment, ShippingStatus

class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ["id", "order_id", "user_id", "address", "status", "tracking_number", "estimated_delivery", "created_at", "updated_at"]
        read_only_fields = ["id", "order_id", "user_id", "created_at", "updated_at"]

class CreateShipmentSerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=255)
    address  = serializers.CharField(help_text="Shipping address")
    user_id  = serializers.CharField(max_length=255, required=False, allow_blank=True)
