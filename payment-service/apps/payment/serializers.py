"""
apps/payment/serializers.py
DRF Serializers for Payment
"""
from rest_framework import serializers
from .models import Payment, PaymentMethod

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order_id", "user_id", "amount", "status", "payment_method", "transaction_id", "created_at", "updated_at"]
        read_only_fields = ["id", "user_id", "status", "transaction_id", "created_at", "updated_at"]

class ProcessPaymentSerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=255)
    amount   = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices, default=PaymentMethod.CREDIT_CARD)
    # simulated boolean to force success/failure for testing
    simulate_success = serializers.BooleanField(default=True, help_text="Set to False to simulate a failed payment")
