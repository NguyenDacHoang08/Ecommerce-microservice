"""
apps/shipping/urls.py
URLs for Shipping operations.
"""
from django.urls import path
from .views import (
    ShipmentDetailView,
    ShipmentCreateView,
    ShipmentListView,
    ShipmentRetrieveUpdateView,
)

urlpatterns = [
    path("", ShipmentListView.as_view(), name="shipping-list"),
    path("create/", ShipmentCreateView.as_view(), name="shipping-create"),
    path("status/<str:order_id>/", ShipmentDetailView.as_view(), name="shipping-detail"),
    path("<uuid:pk>/", ShipmentRetrieveUpdateView.as_view(), name="shipping-detail-by-id"),
]
