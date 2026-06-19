"""
apps/cart/views.py
API Views for Cart operations.
"""
import requests
import logging
from django.conf import settings
from rest_framework import status, views, permissions
from rest_framework.response import Response
from django.db import transaction

from .models import Cart, CartItem
from .serializers import CartSerializer, AddItemSerializer, UpdateItemSerializer

logger = logging.getLogger(__name__)

class CartBaseView(views.APIView):
    """Base view to handle getting or creating a cart for the user."""
    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self, request):
        user_id = str(request.user.id) # Assuming JWT auth provides request.user
        cart, created = Cart.objects.get_or_create(user_id=user_id)
        if created:
            logger.info(f"Created new cart for user {user_id}")
        return cart

    def check_product_availability(self, product_id, required_quantity):
        """
        Calls the Product Service to check if the product is available
        and has enough stock.
        """
        try:
            url = f"{settings.PRODUCT_SERVICE_URL}/api/products/{product_id}/availability/"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 404:
                return False, "Product not found."
                
            if response.status_code == 200:
                data = response.json()
                is_available = data.get("is_available", False)
                stock_quantity = data.get("quantity", 0)
                
                if not is_available:
                    return False, "Product is currently unavailable."
                if stock_quantity < required_quantity:
                    return False, f"Not enough stock. Only {stock_quantity} available."
                    
                return True, "Available"
                
            return False, f"Failed to check product status. Service returned {response.status_code}."
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with product-service: {e}")
            return False, "Error communicating with product service."


class CartDetailView(CartBaseView):
    """
    GET /cart/
    Retrieve the current user's cart and its items.
    """
    def get(self, request):
        cart = self.get_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartAddView(CartBaseView):
    """
    POST /cart/add/
    Add an item to the cart. If it already exists, update the quantity.
    """
    def post(self, request):
        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        
        cart = self.get_cart(request)
        
        with transaction.atomic():
            # Check if item already exists in cart to calculate total required quantity
            item, created = CartItem.objects.select_for_update().get_or_create(
                cart=cart, 
                product_id=product_id,
                defaults={'quantity': 0}
            )
            
            new_quantity = item.quantity + quantity
            
            # Verify with Product Service
            is_available, message = self.check_product_availability(product_id, new_quantity)
            if not is_available:
                if created:
                    item.delete() # Revert creation if not enough stock
                return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
            
            item.quantity = new_quantity
            item.save()
            cart.save() # trigger updated_at
            
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartItemRemoveView(CartBaseView):
    """
    DELETE /cart/remove/<item_id>/
    Remove a specific item from the cart.
    """
    def delete(self, request, item_id):
        cart = self.get_cart(request)
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
            cart.save() # trigger updated_at
            return Response({"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found in your cart."}, status=status.HTTP_404_NOT_FOUND)


class CartClearView(CartBaseView):
    """
    DELETE /cart/clear/
    Remove all items from the cart.
    """
    def delete(self, request):
        cart = self.get_cart(request)
        cart.clear()
        return Response({"message": "Cart cleared successfully."}, status=status.HTTP_204_NO_CONTENT)


class CartItemUpdateView(CartBaseView):
    """
    PATCH /cart/update/<item_id>/
    Update the quantity of a specific item in the cart.
    """
    def patch(self, request, item_id):
        cart = self.get_cart(request)
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found in your cart."}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = UpdateItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_quantity = serializer.validated_data['quantity']
        
        with transaction.atomic():
            # Verify with Product Service
            is_available, message = self.check_product_availability(item.product_id, new_quantity)
            if not is_available:
                return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
                
            item.update_quantity(new_quantity)
            cart.save() # trigger updated_at
            
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
