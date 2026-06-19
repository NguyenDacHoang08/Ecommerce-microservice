"""
apps/orders/views.py
API Views for Order operations.
"""
import requests
import logging
from django.conf import settings
from rest_framework import status, views, permissions, generics
from rest_framework.response import Response
from django.db import transaction

from .models import Order, OrderItem, OrderStatus
from .serializers import OrderSerializer, CreateOrderSerializer

logger = logging.getLogger(__name__)

class OrderListView(generics.ListAPIView):
    """
    GET /orders/
    Retrieve all orders for the current user.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        is_staff_user = getattr(user, "is_staff", False) or (hasattr(user, "token") and user.token.get("role") in ["admin", "staff"])
        if is_staff_user:
            return Order.objects.all()
        return Order.objects.filter(user_id=str(user.id))

    def _get_auth_headers(self, request):
        """Pass the user's JWT token to other services."""
        auth_header = request.headers.get('Authorization')
        return {'Authorization': auth_header} if auth_header else {}

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        headers = self._get_auth_headers(request)
        user_id = str(request.user.id)

        try:
            # 1. Fetch Cart
            cart_url = f"{settings.CART_SERVICE_URL}/cart/"
            cart_resp = requests.get(cart_url, headers=headers, timeout=5)
            
            if cart_resp.status_code != 200:
                return Response({"error": "Failed to fetch cart."}, status=status.HTTP_400_BAD_REQUEST)
                
            cart_data = cart_resp.json()
            items = cart_data.get("items", [])
            
            if not items:
                return Response({"error": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

            order_items_data = []
            
            # Use a transaction for local DB operations
            with transaction.atomic():
                # Create the Order first (status PROCESSING)
                order = Order.objects.create(user_id=user_id, status=OrderStatus.PROCESSING)
                
                # Process each item
                for item in items:
                    product_id = item["product_id"]
                    quantity = item["quantity"]
                    
                    # 2. Fetch Product Details (for price)
                    prod_url = f"{settings.PRODUCT_SERVICE_URL}/api/products/{product_id}/"
                    prod_resp = requests.get(prod_url, headers=headers, timeout=5)
                    
                    if prod_resp.status_code != 200:
                        raise ValueError(f"Failed to fetch product details for {product_id}.")
                        
                    prod_data = prod_resp.json()
                    price = prod_data.get("effective_price", prod_data.get("price"))
                    
                    if price is None:
                        raise ValueError(f"Price not available for product {product_id}.")

                    # 3 & 4. Reserve Stock
                    reserve_url = f"{settings.PRODUCT_SERVICE_URL}/api/products/{product_id}/reserve-stock/"
                    reserve_payload = {"quantity": quantity}
                    reserve_resp = requests.post(reserve_url, json=reserve_payload, headers=headers, timeout=5)
                    
                    if reserve_resp.status_code != 200:
                        error_msg = reserve_resp.json().get("detail", "Stock reservation failed.")
                        raise ValueError(f"Product {product_id}: {error_msg}")

                    # 5. Create OrderItem
                    OrderItem.objects.create(
                        order=order,
                        product_id=product_id,
                        quantity=quantity,
                        price=price
                    )
                
                # Calculate total
                order.calculate_total()
                order.save()
            
            # If transaction is successful, perform non-transactional external side-effects
            
            # 6. Clear Cart
            clear_url = f"{settings.CART_SERVICE_URL}/cart/clear/"
            requests.delete(clear_url, headers=headers, timeout=5)
            
            # 7. Call Payment Service (Simulated/Stubbed)
            logger.info(f"Order {order.id} created successfully. Calling payment service...")
            # Example: 
            # payment_url = f"{settings.PAYMENT_SERVICE_URL}/payments/process/"
            # requests.post(payment_url, json={"order_id": str(order.id), "amount": str(order.total_price)}, headers=headers)

            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # Domain/Business logic error (e.g., out of stock)
            # Note: If stock was partially reserved, a real system would need 
            # a saga pattern or compensation transaction to release the stock here.
            # For simplicity in this demo, we assume failure happens before full reservation
            # or requires manual reconciliation.
            logger.error(f"Order creation failed: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during order creation: {e}")
            return Response({"error": "Internal communication error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception("Unexpected error during order creation")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /orders/<id>/
    PATCH /orders/<id>/
    DELETE /orders/<id>/
    Retrieve, update or delete a specific order.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        is_staff_user = getattr(user, "is_staff", False) or (hasattr(user, "token") and user.token.get("role") in ["admin", "staff"])
        if is_staff_user:
            return Order.objects.all()
        return Order.objects.filter(user_id=str(user.id))

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        instance = serializer.save()

        # When status transitions to CONFIRMED, auto-create a shipment
        if old_status != "CONFIRMED" and instance.status == "CONFIRMED":
            self._create_shipment(instance)

    def _create_shipment(self, order):
        """Call the Shipping Service to create a shipment for a confirmed order."""
        import requests
        from django.conf import settings as django_settings
        try:
            shipping_url = f"{django_settings.SHIPPING_SERVICE_URL}/shipping/create/"
            auth_header = self.request.headers.get("Authorization")
            headers = {"Authorization": auth_header} if auth_header else {}
            # Build a basic address from available order info
            address = f"Order #{order.id}"
            requests.post(
                shipping_url,
                json={"order_id": str(order.id), "address": address, "user_id": str(order.user_id)},
                headers=headers,
                timeout=5,
            )
            logger.info(f"Shipment creation requested for confirmed order {order.id}")
        except Exception as e:
            logger.error(f"Failed to create shipment for order {order.id}: {e}")

    def perform_destroy(self, instance):
        user = self.request.user
        is_staff_user = getattr(user, "is_staff", False) or (hasattr(user, "token") and user.token.get("role") in ["admin", "staff"])
        if not is_staff_user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only staff members can delete orders.")
        instance.delete()
