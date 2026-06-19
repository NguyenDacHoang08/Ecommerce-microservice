"""
apps/payment/views.py
API Views for Payment operations.
"""
import requests
import logging
import uuid
import time
from django.conf import settings
from rest_framework import status, views, permissions, generics
from rest_framework.response import Response

from .models import Payment
from .serializers import PaymentSerializer, ProcessPaymentSerializer

logger = logging.getLogger(__name__)

class PaymentDetailView(generics.RetrieveAPIView):
    """
    GET /payment/status/<order_id>/
    Retrieve the payment status for a specific order.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'order_id'

    def get_queryset(self):
        return Payment.objects.filter(user_id=str(self.request.user.id))

class PaymentProcessView(views.APIView):
    """
    POST /payment/pay/
    Process a payment for an order.
    Simulates payment gateway integration.
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_auth_headers(self, request):
        """Pass the user's JWT token to other services."""
        auth_header = request.headers.get('Authorization')
        return {'Authorization': auth_header} if auth_header else {}

    def post(self, request):
        serializer = ProcessPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        amount = serializer.validated_data['amount']
        payment_method = serializer.validated_data['payment_method']
        simulate_success = serializer.validated_data['simulate_success']
        
        user_id = str(request.user.id)
        
        # 1. Verify if payment already exists for this order
        payment, created = Payment.objects.get_or_create(
            order_id=order_id,
            defaults={
                'user_id': user_id,
                'amount': amount,
                'payment_method': payment_method
            }
        )
        
        if not created and payment.status == 'SUCCESS':
            return Response({"message": "Order is already paid.", "payment": PaymentSerializer(payment).data}, status=status.HTTP_400_BAD_REQUEST)

        # Update amount/method if it's a retry
        if not created:
            payment.amount = amount
            payment.payment_method = payment_method
            payment.save()

        # 2. Simulate Payment Processing Delay
        logger.info(f"Processing payment for order {order_id}...")
        time.sleep(1) # Fake processing time
        
        if simulate_success:
            transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
            payment.mark_as_success(transaction_id=transaction_id)
            logger.info(f"Payment successful for order {order_id}. Txn: {transaction_id}")
            
            # 3. Notify Order Service and Shipping Service (Event/Webhook simulation)
            self._notify_other_services(request, order_id, "PAID")
            
        else:
            payment.mark_as_failed()
            logger.warning(f"Payment failed for order {order_id}.")
            self._notify_other_services(request, order_id, "PAYMENT_FAILED")
            
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)
        
    def _notify_other_services(self, request, order_id, status_code):
        """
        Simulate sending events or webhooks to other services.
        In a real microservices architecture, this should be done via a Message Broker (RabbitMQ, Kafka, Redis Pub/Sub).
        """
        headers = self._get_auth_headers(request)
        
        # Example of HTTP calls (replace with proper endpoints when implemented in those services)
        try:
            # Order Service Update
            # order_update_url = f"{settings.ORDER_SERVICE_URL}/orders/{order_id}/update-status/"
            # requests.patch(order_update_url, json={"status": status_code}, headers=headers, timeout=3)
            logger.info(f"[SIMULATED EVENT] Notified Order Service: Order {order_id} status changed to {status_code}")
            
            # Shipping Service Update (Only if PAID)
            if status_code == "PAID":
                # shipping_create_url = f"{settings.SHIPPING_SERVICE_URL}/shipping/create/"
                # requests.post(shipping_create_url, json={"order_id": order_id}, headers=headers, timeout=3)
                logger.info(f"[SIMULATED EVENT] Notified Shipping Service: Please create shipment for Order {order_id}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to notify other services for order {order_id}: {e}")
