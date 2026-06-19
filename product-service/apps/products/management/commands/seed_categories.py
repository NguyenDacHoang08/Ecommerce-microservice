"""
Management command: seed_categories
Creates default product categories if they don't exist.

Usage:
  python manage.py seed_categories
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import models
from apps.products.domain.models.product import Category, Product


CATEGORIES = [
    {
        "name": "Electronics",
        "slug": "electronics",
        "description": "Smartphones, Laptops, Tablets, Accessories and more",
    },
    {
        "name": "Fashion",
        "slug": "fashion",
        "description": "Clothing, Shoes, Bags and Accessories",
    },
    {
        "name": "Books",
        "slug": "books",
        "description": "Fiction, Non-fiction, Textbooks and more",
    },
]


class Command(BaseCommand):
    help = "Seed default product categories (Electronics, Fashion, Books only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-create categories even if they already exist",
        )

    def handle(self, *args, **options):
        # 1. Create or update the 3 main categories
        main_categories = {}
        for cat_data in CATEGORIES:
            name = cat_data["name"]
            slug = cat_data["slug"]
            cat, created = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": cat_data["description"],
                    "parent": None,
                    "is_active": True,
                }
            )
            main_categories[slug] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created main category: {name}"))
            else:
                self.stdout.write(f"Updated main category: {name}")

        # 2. Re-assign products that belong to other categories
        all_categories = Category.objects.all()
        for category in all_categories:
            if category.slug in main_categories:
                continue
            
            # Determine which main category to assign products to
            target_slug = "electronics" # fallback
            c_slug = category.slug.lower()
            c_name = category.name.lower()
            
            if any(x in c_slug or x in c_name for x in ["fashion", "cloth", "shoe", "bag", "wear"]):
                target_slug = "fashion"
            elif any(x in c_slug or x in c_name for x in ["book", "read", "novel", "textbook", "fiction"]):
                target_slug = "books"
            elif any(x in c_slug or x in c_name for x in ["electronic", "phone", "laptop", "tablet", "accessory", "smart"]):
                target_slug = "electronics"
            elif category.parent:
                p_slug = category.parent.slug.lower()
                if "fashion" in p_slug:
                    target_slug = "fashion"
                elif "book" in p_slug:
                    target_slug = "books"
                elif "electronic" in p_slug:
                    target_slug = "electronics"
            
            target_cat = main_categories[target_slug]
            
            # Reassign products
            products_to_move = Product.objects.filter(category=category)
            if products_to_move.exists():
                count = products_to_move.update(category=target_cat)
                self.stdout.write(f"Moved {count} products from category '{category.name}' to '{target_cat.name}'")

        # 3. Delete all other categories
        other_cats = Category.objects.exclude(slug__in=main_categories.keys())
        if other_cats.exists():
            deleted_count, _ = other_cats.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} old/unused categories."))

        self.stdout.write(self.style.SUCCESS("\nDone seeding categories."))
