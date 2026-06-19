"""
Management command: seed_shipments
Seeds shipments in shipping-service corresponding to the seeded orders.

Usage:
  python manage.py seed_shipments
"""
from django.core.management.base import BaseCommand
from apps.shipping.models import Shipment, ShippingStatus
import uuid

# User ID matches the customer user
CUSTOMER_USER_ID = "6f70f589-9437-4724-a3b4-405385794a82"

# Map of seeded orders and their corresponding shipping status
ORDER_SHIPMENTS = [
    {
        "order_id": "5129c7b9-9ed0-4aea-8b39-1ff02373fe93",  # Confirmed
        "status": ShippingStatus.PROCESSING,
        "address": "123 Seed Street, Ward 5, District 1, Ho Chi Minh City",
    },
    {
        "order_id": "11223344-5566-7788-9900-aabbccddeeff",  # Confirmed
        "status": ShippingStatus.PROCESSING,
        "address": "456 Oak Avenue, Ward 10, District 3, Ho Chi Minh City",
    },
    {
        "order_id": "3dde91bf-6ba5-4c16-88dd-382ca0a13ddd",  # Delivered
        "status": ShippingStatus.DELIVERED,
        "address": "789 Pine Road, Ben Nghe Ward, District 1, Ho Chi Minh City",
    },
    {
        "order_id": "22334455-6677-8899-00aa-bbccddeeff11",  # Delivered
        "status": ShippingStatus.DELIVERED,
        "address": "101 Maple Boulevard, Thao Dien Ward, District 2, Ho Chi Minh City",
    }
]

class Command(BaseCommand):
    help = "Seed shipments for seeded orders"

    def handle(self, *args, **options):
        self.stdout.write("Starting shipment seeding...")

        # Clear existing shipments
        Shipment.objects.all().delete()
        self.stdout.write("Cleared existing shipments.")

        for item in ORDER_SHIPMENTS:
            shipment, created = Shipment.objects.update_or_create(
                order_id=item["order_id"],
                defaults={
                    "user_id": CUSTOMER_USER_ID,
                    "status": item["status"],
                    "address": item["address"]
                }
            )
            self.stdout.write(f"Processed Shipment for Order {item['order_id']} (Status: {item['status']})")

        self.stdout.write(self.style.SUCCESS("Shipment seeding completed successfully!"))
