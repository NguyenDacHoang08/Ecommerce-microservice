"""
Management command: seed_products
Creates a set of realistic seed products with detailed attributes and image URLs.

Usage:
  python manage.py seed_products
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from decimal import Decimal
import uuid

from apps.products.domain.models.product import (
    Category,
    Product,
    ElectronicsProduct,
    FashionProduct,
    Book,
    ProductImage,
    ProductStatus
)

class Command(BaseCommand):
    help = "Seed realistic products into the database"

    def handle(self, *args, **options):
        self.stdout.write("Starting product seeding...")

        # 1. Fetch categories
        try:
            electronics_cat = Category.objects.get(slug="electronics")
            fashion_cat = Category.objects.get(slug="fashion")
            books_cat = Category.objects.get(slug="books")
        except Category.DoesNotExist:
            self.stdout.write(self.style.ERROR("Categories must exist first! Please run 'seed_categories'."))
            return

        # Seller ID from user service (e.g., admin or seller account)
        seller_id = uuid.UUID("fc49fe16-5478-4503-8dd0-3172717fd695")

        # 2. Electronics Products (Original 8 + 10 New = 18 total)
        electronics_data = [
            {
                "name": "iPhone 15 Pro Max",
                "sku": "IPHONE15PM-1",
                "description": "Titanium design, A17 Pro chip, powerful camera system, and USB-C.",
                "price": Decimal("29990000.00"),
                "quantity": 50,
                "brand": "Apple",
                "model_number": "A3106",
                "warranty_months": 12,
                "connectivity": ["5G", "Wi-Fi 6E", "Bluetooth 5.3"],
                "image_url": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Sony WH-1000XM5 Headphones",
                "sku": "SONYXM5-1",
                "description": "Industry-leading noise cancelling wireless headphones with exceptional sound quality.",
                "price": Decimal("6490000.00"),
                "quantity": 100,
                "brand": "Sony",
                "model_number": "WH1000XM5",
                "warranty_months": 12,
                "connectivity": ["Bluetooth 5.2", "NFC"],
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Dell XPS 13 Laptop",
                "sku": "DELLXPS13-1",
                "description": "Stunning 13.4-inch display, Intel Core i7, 16GB RAM, 512GB SSD in a thin and light design.",
                "price": Decimal("32500000.00"),
                "quantity": 20,
                "brand": "Dell",
                "model_number": "XPS9315",
                "warranty_months": 24,
                "connectivity": ["Wi-Fi 6", "Bluetooth 5.1"],
                "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Samsung Galaxy S24 Ultra",
                "sku": "SAMS24U-1",
                "description": "Galaxy AI is here. 200MP camera, built-in S Pen, and Snapdragon 8 Gen 3 for Galaxy.",
                "price": Decimal("27990000.00"),
                "quantity": 40,
                "brand": "Samsung",
                "model_number": "SM-S928B",
                "warranty_months": 12,
                "connectivity": ["5G", "Wi-Fi 7", "Bluetooth 5.3"],
                "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "MacBook Pro 14 M3",
                "sku": "MACBOOKM3-1",
                "description": "Apple M3 chip, 8-core CPU, 10-core GPU, 8GB unified memory, 512GB SSD storage.",
                "price": Decimal("39990000.00"),
                "quantity": 15,
                "brand": "Apple",
                "model_number": "MR7J3",
                "warranty_months": 12,
                "connectivity": ["Wi-Fi 6E", "Bluetooth 5.3"],
                "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Nintendo Switch OLED",
                "sku": "NSWITCH-OLED",
                "description": "Vibrant 7-inch OLED screen, wide adjustable stand, wired LAN port, and 64 GB internal storage.",
                "price": Decimal("7500000.00"),
                "quantity": 60,
                "brand": "Nintendo",
                "model_number": "HEG-001",
                "warranty_months": 12,
                "connectivity": ["Wi-Fi", "Bluetooth 4.1"],
                "image_url": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Sony PlayStation 5 Slim",
                "sku": "PS5SLIM-1",
                "description": "Experience lightning-fast loading with an ultra-high speed SSD, deeper immersion, and an all-new generation of incredible games.",
                "price": Decimal("13990000.00"),
                "quantity": 30,
                "brand": "Sony",
                "model_number": "CFI-2000",
                "warranty_months": 12,
                "connectivity": ["Wi-Fi 6", "Bluetooth 5.1", "HDMI 2.1"],
                "image_url": "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Apple Watch Series 9",
                "sku": "AWATCH9-1",
                "description": "S9 SiP chip, a magically gesture-free way to use watch, double tap gesture, and brighter display.",
                "price": Decimal("9990000.00"),
                "quantity": 45,
                "brand": "Apple",
                "model_number": "A2978",
                "warranty_months": 12,
                "connectivity": ["Wi-Fi", "Bluetooth 5.3", "NFC"],
                "image_url": "https://images.unsplash.com/photo-1434494878577-86c23bcb06b9?w=500&auto=format&fit=crop&q=60"
            },
            # 10 NEW Electronics products
            {
                "name": "iPad Air 5",
                "sku": "IPADAIR5-1",
                "description": "Apple M1 chip, 10.9-inch Liquid Retina display, 64GB storage, Wi-Fi 6.",
                "price": Decimal("15990000.00"),
                "quantity": 35,
                "brand": "Apple",
                "model_number": "MM9F3ZP/A",
                "warranty_months": 12,
                "connectivity": ["Wi-Fi 6", "Bluetooth 5.0"],
                "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "GoPro Hero 12 Black",
                "sku": "GOPRO12-1",
                "description": "Incredible image quality, even better HyperSmooth video stabilization, and a huge boost in battery life.",
                "price": Decimal("10490000.00"),
                "quantity": 40,
                "brand": "GoPro",
                "model_number": "CHDHX-121-RW",
                "warranty_months": 12,
                "connectivity": ["Wi-Fi", "Bluetooth 5.2"],
                "image_url": "https://images.unsplash.com/photo-1565849906663-747bab300df9?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "DJI Mavic 3 Pro",
                "sku": "DJIMAVIC3-1",
                "description": "Triple-camera system drone. 4/3 CMOS Hasselblad camera, 28x hybrid zoom, 43 min flight time.",
                "price": Decimal("49990000.00"),
                "quantity": 10,
                "brand": "DJI",
                "model_number": "CP.MA.00000654.01",
                "warranty_months": 12,
                "connectivity": ["O3+", "Wi-Fi", "Bluetooth 5.1"],
                "image_url": "https://images.unsplash.com/photo-1508614589041-895b88991e3e?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Bose QuietComfort Ultra",
                "sku": "BOSEQCU-1",
                "description": "World-class noise cancellation, breakthrough spatialized audio, and premium design.",
                "price": Decimal("8990000.00"),
                "quantity": 50,
                "brand": "Bose",
                "model_number": "880052-0010",
                "warranty_months": 12,
                "connectivity": ["Bluetooth 5.3"],
                "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Kindle Paperwhite 5",
                "sku": "KINDLEPW5-1",
                "description": "6.8-inch display, thinner borders, adjustable warm light, up to 10 weeks of battery life.",
                "price": Decimal("3890000.00"),
                "quantity": 120,
                "brand": "Amazon",
                "model_number": "M2L3EK",
                "warranty_months": 12,
                "connectivity": ["Wi-Fi", "Bluetooth"],
                "image_url": "https://images.unsplash.com/photo-1594980596870-8aa52a78d8cd?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Marshall Acton III Speaker",
                "sku": "MARSHALLACTON-1",
                "description": "The most compact Bluetooth speaker in the home line-up, has an even wider soundstage than its predecessor.",
                "price": Decimal("6790000.00"),
                "quantity": 30,
                "brand": "Marshall",
                "model_number": "ACTON-III",
                "warranty_months": 12,
                "connectivity": ["Bluetooth 5.2", "AUX 3.5mm"],
                "image_url": "https://images.unsplash.com/photo-1612444530582-fc66183b16f7?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Keychron K2 V2 Keyboard",
                "sku": "KEYCHRONK2-1",
                "description": "A 75% layout wireless mechanical keyboard. Tactile Gateron switches, RGB backlight.",
                "price": Decimal("1950000.00"),
                "quantity": 75,
                "brand": "Keychron",
                "model_number": "K2-V2",
                "warranty_months": 12,
                "connectivity": ["Bluetooth 5.1", "USB-C"],
                "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Logitech MX Master 3S Mouse",
                "sku": "LOGMX3S-1",
                "description": "An iconic mouse remastered. Quiet Clicks and 8K DPI tracking for any surface.",
                "price": Decimal("2490000.00"),
                "quantity": 110,
                "brand": "Logitech",
                "model_number": "910-006561",
                "warranty_months": 12,
                "connectivity": ["Logi Bolt", "Bluetooth Low Energy"],
                "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "ASUS TUF Gaming Monitor",
                "sku": "ASUSTUFMON-1",
                "description": "27-inch Full HD (1920x1080) IPS gaming monitor with ultra-fast 165Hz refresh rate.",
                "price": Decimal("5490000.00"),
                "quantity": 25,
                "brand": "ASUS",
                "model_number": "VG279Q1A",
                "warranty_months": 36,
                "connectivity": ["DisplayPort 1.2", "HDMI 1.4", "Earphone Jack"],
                "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Canon EOS R50 Camera",
                "sku": "CANONR50-1",
                "description": "Compact and lightweight mirrorless camera with 24.2 Megapixel CMOS sensor and DIGIC X image processor.",
                "price": Decimal("18990000.00"),
                "quantity": 15,
                "brand": "Canon",
                "model_number": "EOS-R50-KIT",
                "warranty_months": 24,
                "connectivity": ["Wi-Fi", "Bluetooth 4.2", "USB-C", "HDMI Micro"],
                "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500&auto=format&fit=crop&q=60"
            }
        ]

        for item in electronics_data:
            prod, created = ElectronicsProduct.objects.update_or_create(
                sku=item["sku"],
                defaults={
                    "name": item["name"],
                    "slug": slugify(item["name"]),
                    "description": item["description"],
                    "category": electronics_cat,
                    "seller_id": seller_id,
                    "price": item["price"],
                    "quantity": item["quantity"],
                    "brand": item["brand"],
                    "model_number": item["model_number"],
                    "warranty_months": item["warranty_months"],
                    "connectivity": item["connectivity"],
                    "status": ProductStatus.ACTIVE
                }
            )
            ProductImage.objects.update_or_create(
                product=prod,
                url=item["image_url"],
                defaults={"alt_text": item["name"], "is_primary": True}
            )
            self.stdout.write(f"Processed Electronics: {item['name']}")

        # 3. Fashion Products (Original 8 + 10 New = 18 total)
        fashion_data = [
            {
                "name": "Nike Air Max 90",
                "sku": "NIKEAM90-1",
                "description": "Classic design meets modern comfort. Durable leather and mesh upper with signature Air unit.",
                "price": Decimal("3500000.00"),
                "quantity": 75,
                "brand": "Nike",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "Leather and Mesh",
                "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Levi's 501 Original Jeans",
                "sku": "LEVI501-1",
                "description": "The original straight fit jean since 1873. Made with premium non-stretch denim.",
                "price": Decimal("1250000.00"),
                "quantity": 120,
                "brand": "Levi's",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "100% Cotton Denim",
                "image_url": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Zara Leather Bomber Jacket",
                "sku": "ZARALB-1",
                "description": "Crafted from soft, supple sheepskin leather. A timeless classic jacket for any wardrobe.",
                "price": Decimal("2400000.00"),
                "quantity": 30,
                "brand": "Zara",
                "gender": FashionProduct.Gender.MALE,
                "material": "Sheepskin Leather",
                "image_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Adidas Ultraboost Light",
                "sku": "ADIULTRAL-1",
                "description": "Experience epic energy with the new Ultraboost Light, our lightest Ultraboost ever.",
                "price": Decimal("4200000.00"),
                "quantity": 55,
                "brand": "Adidas",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "Primeknit / Boost Foam",
                "image_url": "https://images.unsplash.com/photo-1587563871167-1ee9c731aefb?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Ralph Lauren Polo Shirt",
                "sku": "RLPOLO-1",
                "description": "Classic Fit Mesh Polo Shirt. A signature design with the iconic embroidered pony.",
                "price": Decimal("1800000.00"),
                "quantity": 90,
                "brand": "Ralph Lauren",
                "gender": FashionProduct.Gender.MALE,
                "material": "100% Cotton Mesh",
                "image_url": "https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Uniqlo AIRism T-Shirt",
                "sku": "UNIQLOAIR-1",
                "description": "Cotton blend AIRism fabric looks like classic cotton but feels smooth, light, and dry.",
                "price": Decimal("390000.00"),
                "quantity": 250,
                "brand": "Uniqlo",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "AIRism Poly-Cotton",
                "image_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Nike Club Fleece Hoodie",
                "sku": "NIKEHOODIE-1",
                "description": "A cozy closet staple, the Nike Club Fleece Hoodie combines classic style with the soft comfort of fleece.",
                "price": Decimal("1450000.00"),
                "quantity": 80,
                "brand": "Nike",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "80% Cotton / 20% Polyester",
                "image_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Converse Chuck Taylor 70",
                "sku": "CHUCK70-1",
                "description": "The Chuck 70 mixes the best details from the '70s-era Chuck with impeccable craftsmanship and premium materials.",
                "price": Decimal("1900000.00"),
                "quantity": 110,
                "brand": "Converse",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "Premium Organic Canvas",
                "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=500&auto=format&fit=crop&q=60"
            },
            # 10 NEW Fashion products
            {
                "name": "H&M Slim Fit Chinos",
                "sku": "HMCHINOS-1",
                "description": "Chinos in washed cotton twill. Slim fit with side pockets and welt back pockets.",
                "price": Decimal("590000.00"),
                "quantity": 140,
                "brand": "H&M",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "98% Cotton / 2% Elastane",
                "image_url": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Adidas Adilette Slides",
                "sku": "ADIADILETTE-1",
                "description": "Quick-drying polyurethane bandage upper with iconic 3-Stripes, contoured footbed.",
                "price": Decimal("790000.00"),
                "quantity": 200,
                "brand": "Adidas",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "Synthetic",
                "image_url": "https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Ray-Ban Classic Wayfarer",
                "sku": "RAYBANWAY-1",
                "description": "Original Wayfarer Classics are the most recognizable style in the history of sunglasses.",
                "price": Decimal("3450000.00"),
                "quantity": 65,
                "brand": "Ray-Ban",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "Acetate Frame",
                "image_url": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Calvin Klein T-Shirt Pack",
                "sku": "CKUNDER-1",
                "description": "Pure cotton fabrication, crew neckline, Calvin Klein branding on the chest.",
                "price": Decimal("950000.00"),
                "quantity": 150,
                "brand": "Calvin Klein",
                "gender": FashionProduct.Gender.MALE,
                "material": "100% Cotton",
                "image_url": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Zara Plaid Overshirt",
                "sku": "ZARAPLAID-1",
                "description": "Oversized fit shirt featuring a collared neckline, long sleeves with buttoned cuffs, patch chest pockets.",
                "price": Decimal("1290000.00"),
                "quantity": 85,
                "brand": "Zara",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "Cotton Flannel Blend",
                "image_url": "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Puma Suede Classic",
                "sku": "PUMASUEDE-1",
                "description": "The sport classic has remained a legendary sneaker since the 1960s. Premium suede upper.",
                "price": Decimal("1850000.00"),
                "quantity": 95,
                "brand": "Puma",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "Premium Suede",
                "image_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Champion Reverse Weave Sweatshirt",
                "sku": "CHAMPSWEAT-1",
                "description": "Heavyweight fleece features a loose fit, signature stretch side panels, and durable double-needle construction.",
                "price": Decimal("1350000.00"),
                "quantity": 100,
                "brand": "Champion",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "82% Cotton / 18% Polyester",
                "image_url": "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Lacoste Classic L1212 Polo",
                "sku": "LACOSTECLASSIC-1",
                "description": "The signature polo shirt. Knit in fine cotton petit piqué for both breathability and elegance.",
                "price": Decimal("2600000.00"),
                "quantity": 70,
                "brand": "Lacoste",
                "gender": FashionProduct.Gender.MALE,
                "material": "100% Cotton Petit Piqué",
                "image_url": "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Herschel Little America Backpack",
                "sku": "HERSCHELBACK-1",
                "description": "An iconic mountaineering style backpack. Signature striped fabric liner, padded and fleece lined 15-inch laptop sleeve.",
                "price": Decimal("2450000.00"),
                "quantity": 60,
                "brand": "Herschel",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "Polyester Canvas",
                "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Birkenstock Arizona Sandals",
                "sku": "BIRKENARIZONA-1",
                "description": "The legendary two-strap design from Birkenstock. Iconic cork-latex footbed mimics the natural shape of the foot.",
                "price": Decimal("2850000.00"),
                "quantity": 80,
                "brand": "Birkenstock",
                "gender": FashionProduct.Gender.UNISEX,
                "material": "Birko-Flor / Suede Leather",
                "image_url": "https://images.unsplash.com/photo-1603487988353-c80155b76d3f?w=500&auto=format&fit=crop&q=60"
            }
        ]

        for item in fashion_data:
            prod, created = FashionProduct.objects.update_or_create(
                sku=item["sku"],
                defaults={
                    "name": item["name"],
                    "slug": slugify(item["name"]),
                    "description": item["description"],
                    "category": fashion_cat,
                    "seller_id": seller_id,
                    "price": item["price"],
                    "quantity": item["quantity"],
                    "brand": item["brand"],
                    "gender": item["gender"],
                    "material": item["material"],
                    "status": ProductStatus.ACTIVE
                }
            )
            ProductImage.objects.update_or_create(
                product=prod,
                url=item["image_url"],
                defaults={"alt_text": item["name"], "is_primary": True}
            )
            self.stdout.write(f"Processed Fashion: {item['name']}")

        # 4. Books (Original 7 + 10 New = 17 total)
        books_data = [
            {
                "name": "Clean Code",
                "sku": "CLEANCODE-1",
                "description": "A Handbook of Agile Software Craftsmanship by Robert C. Martin. A must-read for any software developer.",
                "price": Decimal("380000.00"),
                "quantity": 150,
                "author": "Robert C. Martin",
                "isbn": "9780132350884",
                "publisher": "Prentice Hall",
                "pages": 464,
                "genre": "Software Engineering",
                "image_url": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Harry Potter and the Sorcerer's Stone",
                "sku": "HPSTONE-1",
                "description": "The first novel in the Harry Potter series by J.K. Rowling. Step into the wizarding world of Hogwarts.",
                "price": Decimal("220000.00"),
                "quantity": 200,
                "author": "J.K. Rowling",
                "isbn": "9780439708180",
                "publisher": "Scholastic",
                "pages": 309,
                "genre": "Fantasy",
                "image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Atomic Habits",
                "sku": "HABITS-1",
                "description": "An Easy & Proven Way to Build Good Habits & Break Bad Ones by James Clear.",
                "price": Decimal("180000.00"),
                "quantity": 300,
                "author": "James Clear",
                "isbn": "9780735211292",
                "publisher": "Avery",
                "pages": 320,
                "genre": "Self-Improvement",
                "image_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "The Pragmatic Programmer",
                "sku": "PRAGPROG-1",
                "description": "Your journey to mastery. 20th Anniversary Edition by David Thomas and Andrew Hunt.",
                "price": Decimal("450000.00"),
                "quantity": 80,
                "author": "David Thomas, Andrew Hunt",
                "isbn": "9780135957059",
                "publisher": "Addison-Wesley",
                "pages": 352,
                "genre": "Software Engineering",
                "image_url": "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Design Patterns",
                "sku": "GOFPAT-1",
                "description": "Elements of Reusable Object-Oriented Software by Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides.",
                "price": Decimal("520000.00"),
                "quantity": 70,
                "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides",
                "isbn": "9780201633610",
                "publisher": "Addison-Wesley",
                "pages": 395,
                "genre": "Computer Science",
                "image_url": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Introduction to Algorithms",
                "sku": "CLRSALGO-1",
                "description": "By Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein. The standard bible of algorithm engineering.",
                "price": Decimal("850000.00"),
                "quantity": 40,
                "author": "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein",
                "isbn": "9780262046305",
                "publisher": "MIT Press",
                "pages": 1312,
                "genre": "Computer Science",
                "image_url": "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Refactoring",
                "sku": "REFACMF-1",
                "description": "Improving the Design of Existing Code by Martin Fowler. Learn the art of code smells and refactoring.",
                "price": Decimal("480000.00"),
                "quantity": 95,
                "author": "Martin Fowler",
                "isbn": "9780134757599",
                "publisher": "Addison-Wesley",
                "pages": 448,
                "genre": "Software Engineering",
                "image_url": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=500&auto=format&fit=crop&q=60"
            },
            # 10 NEW Books
            {
                "name": "Designing Data-Intensive Applications",
                "sku": "DDIAKLEPP-1",
                "description": "The Big Ideas Behind Reliable, Scalable, and Maintainable Systems by Martin Kleppmann. A definitive guide for backend engineers.",
                "price": Decimal("680000.00"),
                "quantity": 85,
                "author": "Martin Kleppmann",
                "isbn": "9781449373320",
                "publisher": "O'Reilly Media",
                "pages": 611,
                "genre": "Computer Science",
                "image_url": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Introduction to the Theory of Computation",
                "sku": "SIPSERTHEORY-1",
                "description": "The standard introduction text to computational complexity theory, written by Michael Sipser.",
                "price": Decimal("790000.00"),
                "quantity": 30,
                "author": "Michael Sipser",
                "isbn": "9781133187790",
                "publisher": "Cengage Learning",
                "pages": 480,
                "genre": "Theoretical Computer Science",
                "image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "The Clean Coder",
                "sku": "CLEANCODER-1",
                "description": "A Code of Conduct for Professional Programmers by Robert C. Martin. Learn how to be a professional engineer.",
                "price": Decimal("350000.00"),
                "quantity": 130,
                "author": "Robert C. Martin",
                "isbn": "9780137081073",
                "publisher": "Prentice Hall",
                "pages": 256,
                "genre": "Professional Development",
                "image_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Zero to One",
                "sku": "ZEROTOONE-1",
                "description": "Notes on Startups, or How to Build the Future by Peter Thiel. A legendary book about creating new values.",
                "price": Decimal("195000.00"),
                "quantity": 180,
                "author": "Peter Thiel",
                "isbn": "9780804139298",
                "publisher": "Crown Business",
                "pages": 224,
                "genre": "Business & Startups",
                "image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Sapiens: A Brief History of Humankind",
                "sku": "SAPIENSHARARI-1",
                "description": "A provocative book about the history of our species, from ancient ancestors to the modern age by Yuval Noah Harari.",
                "price": Decimal("290000.00"),
                "quantity": 220,
                "author": "Yuval Noah Harari",
                "isbn": "9780062316097",
                "publisher": "Harper",
                "pages": 512,
                "genre": "History",
                "image_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Thinking, Fast and Slow",
                "sku": "THINKFASTSLOW-1",
                "description": "A famous exploration of human cognitive biases and decision making system by Nobel prize laureate Daniel Kahneman.",
                "price": Decimal("270000.00"),
                "quantity": 110,
                "author": "Daniel Kahneman",
                "isbn": "9780374275631",
                "publisher": "Farrar, Straus and Giroux",
                "pages": 499,
                "genre": "Psychology",
                "image_url": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Clean Architecture",
                "sku": "CLEANARCH-1",
                "description": "A Craftsman's Guide to Software Structure and Design by Robert C. Martin. Learn cleanly decoupled components design.",
                "price": Decimal("420000.00"),
                "quantity": 95,
                "author": "Robert C. Martin",
                "isbn": "9780134494166",
                "publisher": "Prentice Hall",
                "pages": 432,
                "genre": "Software Engineering",
                "image_url": "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Compilers: Principles, Techniques, and Tools",
                "sku": "DRAGONBOOK-1",
                "description": "The classic Dragon Book on compilers design. Learn lexical analysis, parsing, and code generation.",
                "price": Decimal("980000.00"),
                "quantity": 20,
                "author": "Alfred V. Aho, Monica S. Lam, Ravi Sethi, Jeffrey D. Ullman",
                "isbn": "9780321486813",
                "publisher": "Addison-Wesley",
                "pages": 1009,
                "genre": "Computer Science",
                "image_url": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "Grokking Algorithms",
                "sku": "GROKALGO-1",
                "description": "An illustrated guide for programmers and other curious people by Aditya Bhargava. Visually learn algorithms.",
                "price": Decimal("320000.00"),
                "quantity": 160,
                "author": "Aditya Bhargava",
                "isbn": "9781617292231",
                "publisher": "Manning Publications",
                "pages": 288,
                "genre": "Computer Science",
                "image_url": "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=500&auto=format&fit=crop&q=60"
            },
            {
                "name": "The Art of Computer Programming (Vol 1)",
                "sku": "TAOCPVOL1-1",
                "description": "Fundamental Algorithms. The seminal text by Donald E. Knuth, laying the foundation for computer algorithms analysis.",
                "price": Decimal("1250000.00"),
                "quantity": 15,
                "author": "Donald E. Knuth",
                "isbn": "9780201896831",
                "publisher": "Addison-Wesley",
                "pages": 672,
                "genre": "Computer Science",
                "image_url": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=500&auto=format&fit=crop&q=60"
            }
        ]

        for item in books_data:
            prod, created = Book.objects.update_or_create(
                sku=item["sku"],
                defaults={
                    "name": item["name"],
                    "slug": slugify(item["name"]),
                    "description": item["description"],
                    "category": books_cat,
                    "seller_id": seller_id,
                    "price": item["price"],
                    "quantity": item["quantity"],
                    "author": item["author"],
                    "isbn": item["isbn"],
                    "publisher": item["publisher"],
                    "pages": item["pages"],
                    "genre": item["genre"],
                    "status": ProductStatus.ACTIVE
                }
            )
            ProductImage.objects.update_or_create(
                product=prod,
                url=item["image_url"],
                defaults={"alt_text": item["name"], "is_primary": True}
            )
            self.stdout.write(f"Processed Book: {item['name']}")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
