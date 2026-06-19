"""
Management command: seed_orders
Seeds realistic orders into the database, and creates corresponding shipments via shipping-service calls for confirmed/delivered ones.

Usage:
  python manage.py seed_orders
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
import uuid
from apps.orders.models import Order, OrderItem, OrderStatus

# Use the existing customer user ID
CUSTOMER_USER_ID = "6f70f589-9437-4724-a3b4-405385794a82"

# Product IDs from seeded products
PRODUCTS = {
    "habits": {
        "id": "f3f3021c-8590-4201-a9a9-85a0e628afda",
        "price": Decimal("180000.00"),
    },
    "harry_potter": {
        "id": "7c59945a-69e4-4f3b-bc53-27e55767d21e",
        "price": Decimal("220000.00"),
    },
    "nike_shoes": {
        "id": "766f0a99-7b75-4c66-ac93-b446c0a01a34",
        "price": Decimal("3500000.00"),
    },
    "sony_headphones": {
        "id": "691adf27-1e20-44f0-94c7-0efd60f499f2",
        "price": Decimal("6490000.00"),
    },
    "clean_code": {
        "id": "10e7de94-d117-4381-ae31-7ff30a59147d",
        "price": Decimal("380000.00"),
    },
    "uniqlo_tshirt": {
        "id": "8e4b4779-1c3a-43c8-9681-e5e99864f244",
        "price": Decimal("390000.00"),
    },
    "adidas_shoes": {
        "id": "32a60e60-9f15-4f24-a4f5-a6930246ec47",
        "price": Decimal("4200000.00"),
    },
    "switch_oled": {
        "id": "9df559e6-80f3-4fa5-80fb-7657623185f2",
        "price": Decimal("7500000.00"),
    },
    "design_patterns": {
        "id": "5da8f7ad-290d-4ab7-8952-45e784daed24",
        "price": Decimal("520000.00"),
    },
    "macbook_m3": {
        "id": "18e81536-b4f1-44a3-b5af-f1b18435aa2f",
        "price": Decimal("39990000.00"),
    },
    "samsung_s24u": {
        "id": "719e2268-3bc8-48e3-970f-04e0e191f0e8",
        "price": Decimal("27990000.00"),
    },
    "pragmatic_prog": {
        "id": "f6bea8c3-2942-4f9f-99b2-551fb73ee32d",
        "price": Decimal("450000.00"),
    }
}

class Command(BaseCommand):
    help = "Seed sample orders and trigger shipments"

    def handle(self, *args, **options):
        self.stdout.write("Starting order seeding...")

        # Clear existing orders
        Order.objects.all().delete()
        self.stdout.write("Cleared existing orders.")

        # Order 1: Processing
        o1 = Order.objects.create(id=uuid.UUID("be8796a4-9ef7-44b9-9544-f8509fdebb7e"), user_id=CUSTOMER_USER_ID, status=OrderStatus.PROCESSING)
        OrderItem.objects.create(order=o1, product_id=PRODUCTS["habits"]["id"], quantity=1, price=PRODUCTS["habits"]["price"])
        OrderItem.objects.create(order=o1, product_id=PRODUCTS["harry_potter"]["id"], quantity=1, price=PRODUCTS["harry_potter"]["price"])
        o1.calculate_total()
        self.stdout.write(f"Created Processing Order {o1.id} (Total: {o1.total_price})")

        # Order 2: Confirmed
        o2 = Order.objects.create(id=uuid.UUID("5129c7b9-9ed0-4aea-8b39-1ff02373fe93"), user_id=CUSTOMER_USER_ID, status=OrderStatus.CONFIRMED)
        OrderItem.objects.create(order=o2, product_id=PRODUCTS["nike_shoes"]["id"], quantity=1, price=PRODUCTS["nike_shoes"]["price"])
        o2.calculate_total()
        self.stdout.write(f"Created Confirmed Order {o2.id} (Total: {o2.total_price})")

        # Order 3: Delivered
        o3 = Order.objects.create(id=uuid.UUID("3dde91bf-6ba5-4c16-88dd-382ca0a13ddd"), user_id=CUSTOMER_USER_ID, status=OrderStatus.DELIVERED)
        OrderItem.objects.create(order=o3, product_id=PRODUCTS["sony_headphones"]["id"], quantity=1, price=PRODUCTS["sony_headphones"]["price"])
        o3.calculate_total()
        self.stdout.write(f"Created Delivered Order {o3.id} (Total: {o3.total_price})")

        # Order 4: Cancelled
        o4 = Order.objects.create(id=uuid.UUID("05954d81-1bc7-49ec-8520-5c2ed284ad1b"), user_id=CUSTOMER_USER_ID, status=OrderStatus.CANCELLED)
        OrderItem.objects.create(order=o4, product_id=PRODUCTS["clean_code"]["id"], quantity=2, price=PRODUCTS["clean_code"]["price"])
        o4.calculate_total()
        self.stdout.write(f"Created Cancelled Order {o4.id} (Total: {o4.total_price})")

        # Order 5: Processing
        o5 = Order.objects.create(id=uuid.UUID("e18146ac-2415-4fa2-bf41-35b91bde442f"), user_id=CUSTOMER_USER_ID, status=OrderStatus.PROCESSING)
        OrderItem.objects.create(order=o5, product_id=PRODUCTS["uniqlo_tshirt"]["id"], quantity=3, price=PRODUCTS["uniqlo_tshirt"]["price"])
        OrderItem.objects.create(order=o5, product_id=PRODUCTS["adidas_shoes"]["id"], quantity=1, price=PRODUCTS["adidas_shoes"]["price"])
        o5.calculate_total()
        self.stdout.write(f"Created Processing Order {o5.id} (Total: {o5.total_price})")

        # Order 6: Confirmed
        o6 = Order.objects.create(id=uuid.UUID("11223344-5566-7788-9900-aabbccddeeff"), user_id=CUSTOMER_USER_ID, status=OrderStatus.CONFIRMED)
        OrderItem.objects.create(order=o6, product_id=PRODUCTS["switch_oled"]["id"], quantity=1, price=PRODUCTS["switch_oled"]["price"])
        OrderItem.objects.create(order=o6, product_id=PRODUCTS["design_patterns"]["id"], quantity=1, price=PRODUCTS["design_patterns"]["price"])
        o6.calculate_total()
        self.stdout.write(f"Created Confirmed Order {o6.id} (Total: {o6.total_price})")

        # Order 7: Delivered
        o7 = Order.objects.create(id=uuid.UUID("22334455-6677-8899-00aa-bbccddeeff11"), user_id=CUSTOMER_USER_ID, status=OrderStatus.DELIVERED)
        OrderItem.objects.create(order=o7, product_id=PRODUCTS["macbook_m3"]["id"], quantity=1, price=PRODUCTS["macbook_m3"]["price"])
        o7.calculate_total()
        self.stdout.write(f"Created Delivered Order {o7.id} (Total: {o7.total_price})")

        # Order 8: Processing
        o8 = Order.objects.create(id=uuid.UUID("33445566-7788-9900-aaee-bbccddeeff22"), user_id=CUSTOMER_USER_ID, status=OrderStatus.PROCESSING)
        OrderItem.objects.create(order=o8, product_id=PRODUCTS["samsung_s24u"]["id"], quantity=1, price=PRODUCTS["samsung_s24u"]["price"])
        OrderItem.objects.create(order=o8, product_id=PRODUCTS["pragmatic_prog"]["id"], quantity=1, price=PRODUCTS["pragmatic_prog"]["price"])
        o8.calculate_total()
        self.stdout.write(f"Created Processing Order {o8.id} (Total: {o8.total_price})")

        self.stdout.write(self.style.SUCCESS("Order seeding completed successfully!"))
