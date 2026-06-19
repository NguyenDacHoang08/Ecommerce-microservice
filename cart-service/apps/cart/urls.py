"""
apps/cart/urls.py
URLs for Cart operations.
"""
from django.urls import path
from .views import (
    CartDetailView,
    CartAddView,
    CartItemUpdateView,
    CartItemRemoveView,
    CartClearView
)

urlpatterns = [
    path("", CartDetailView.as_view(), name="cart-detail"),
    path("add/", CartAddView.as_view(), name="cart-add"),
    path("update/<uuid:item_id>/", CartItemUpdateView.as_view(), name="cart-update-item"),
    path("remove/<uuid:item_id>/", CartItemRemoveView.as_view(), name="cart-remove-item"),
    path("clear/", CartClearView.as_view(), name="cart-clear"),
]
