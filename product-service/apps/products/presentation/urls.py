"""
apps/products/presentation/urls.py
API URL routing using DRF Router + nested routes for variants & images.
"""
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from apps.products.presentation.views import (
    CategoryViewSet,
    ProductViewSet,
    BookViewSet,
    ElectronicsViewSet,
    FashionViewSet,
    ProductVariantViewSet,
    ProductImageViewSet,
)

router = DefaultRouter()

# ── Core Resources ────────────────────────────────────────────────────────────
router.register(r"products/categories", CategoryViewSet,    basename="category")
router.register(r"products",            ProductViewSet,     basename="product")
router.register(r"products/books",      BookViewSet,        basename="book")
router.register(r"products/electronics",ElectronicsViewSet, basename="electronics")
router.register(r"products/fashion",    FashionViewSet,     basename="fashion")

# ── Nested sub-resources ──────────────────────────────────────────────────────
# /products/<product_pk>/variants/
# /products/<product_pk>/images/
variant_router = DefaultRouter()
variant_router.register(r"variants", ProductVariantViewSet, basename="product-variant")

image_router = DefaultRouter()
image_router.register(r"images", ProductImageViewSet, basename="product-image")

urlpatterns = [
    path("api/", include(router.urls)),
    # Nested: /api/products/<product_pk>/variants/
    path("api/products/<str:product_pk>/", include(variant_router.urls)),
    # Nested: /api/products/<product_pk>/images/
    path("api/products/<str:product_pk>/", include(image_router.urls)),
]
