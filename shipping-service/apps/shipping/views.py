"""
apps/shipping/views.py
API Views for Shipping operations.
"""
import logging
import requests
from django.conf import settings
from rest_framework import status, views, permissions, generics
from rest_framework.response import Response

from .models import Shipment
from .serializers import ShipmentSerializer, CreateShipmentSerializer

logger = logging.getLogger(__name__)

class ShipmentDetailView(generics.RetrieveAPIView):
    """
    GET /shipping/status/<order_id>/
    Retrieve the shipping status for a specific order.
    """
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'order_id'

    def get_queryset(self):
        # Users can only view their own shipments
        return Shipment.objects.filter(user_id=str(self.request.user.id))

class ShipmentCreateView(views.APIView):
    """
    POST /shipping/create/
    Create a new shipment for an order.
    Normally called by the Payment Service after successful payment, 
    but can also be triggered directly if user is authenticated and authorized.
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_auth_headers(self, request):
        auth_header = request.headers.get('Authorization')
        return {'Authorization': auth_header} if auth_header else {}

    def post(self, request):
        serializer = CreateShipmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        address = serializer.validated_data['address']
        # If user_id is passed in the body (internal service call), use it; otherwise use the JWT user
        user_id = serializer.validated_data.get('user_id') or str(request.user.id)
        
        # Check if shipment already exists
        if Shipment.objects.filter(order_id=order_id).exists():
            return Response({"error": "Shipment already exists for this order."}, status=status.HTTP_400_BAD_REQUEST)

        # In a fully integrated system, you might verify with the Order Service
        # that the order exists, belongs to the user, and is marked as PAID.
        # For demonstration, we assume the caller (e.g., payment service via token) is valid.
        
        # Verify Order via HTTP Call (Optional but recommended)
        try:
            headers = self._get_auth_headers(request)
            order_url = f"{settings.ORDER_SERVICE_URL}/orders/{order_id}/"
            resp = requests.get(order_url, headers=headers, timeout=3)
            
            if resp.status_code == 404:
                return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not verify order with Order Service: {e}")
            # Depending on business rules, you might proceed or fail here.
            # We will proceed for this implementation.

        # Create Shipment
        shipment = Shipment.objects.create(
            order_id=order_id,
            user_id=user_id,
            address=address
        )
        
        logger.info(f"Shipment created: {shipment.tracking_number} for Order {order_id}")
        
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)


class ShipmentListView(generics.ListAPIView):
    """
    GET /shipping/
    List shipments.
    If the user is staff/admin, return all shipments.
    Otherwise, return only shipments belonging to the logged-in user.
    """
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        is_staff_user = getattr(user, "is_staff", False) or (hasattr(user, "token") and user.token.get("role") in ["admin", "staff"])
        
        if is_staff_user:
            queryset = Shipment.objects.all()
        else:
            queryset = Shipment.objects.filter(user_id=str(user.id))
            
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        return queryset


class ShipmentRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /shipping/<id>/
    PATCH /shipping/<id>/
    DELETE /shipping/<id>/
    Retrieve, update or delete a shipment by ID.
    Only accessible if the user is staff/admin, or if it is their own shipment.
    """
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        is_staff_user = getattr(user, "is_staff", False) or (hasattr(user, "token") and user.token.get("role") in ["admin", "staff"])
        
        if is_staff_user:
            return Shipment.objects.all()
        return Shipment.objects.filter(user_id=str(user.id))

    def perform_update(self, serializer):
        user = self.request.user
        is_staff_user = getattr(user, "is_staff", False) or (hasattr(user, "token") and user.token.get("role") in ["admin", "staff"])
        if not is_staff_user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only staff members can update shipments.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        is_staff_user = getattr(user, "is_staff", False) or (hasattr(user, "token") and user.token.get("role") in ["admin", "staff"])
        if not is_staff_user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only staff members can delete shipments.")
        instance.delete()
