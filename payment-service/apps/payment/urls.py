"""
apps/payment/urls.py
URLs for Payment operations.
"""
from django.urls import path
from .views import (
    PaymentDetailView,
    PaymentProcessView,
)

urlpatterns = [
    path("pay/", PaymentProcessView.as_view(), name="payment-process"),
    path("status/<str:order_id>/", PaymentDetailView.as_view(), name="payment-detail"),
]
