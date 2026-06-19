"""
apps/products/presentation/views.py
ModelViewSet for Category, Product (polymorphic), and Stock actions.
Follows DDD: domain logic stays in models, views are thin.
"""
from __future__ import annotations

import logging
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.products.domain.models.product import (
    Category, Product, Book, ElectronicsProduct, FashionProduct,
    ProductVariant, ProductImage,
)
from apps.products.presentation.serializers import (
    CategorySerializer,
    PolymorphicProductSerializer,
    ProductListSerializer,
    BookSerializer,
    ElectronicsSerializer,
    FashionSerializer,
    ProductVariantSerializer,
    ProductImageSerializer,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Category ViewSet
# ──────────────────────────────────────────────────────────────────────────────

class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for product categories.
    Root categories only returned by default; nested via ?parent=<id>.
    """
    queryset = Category.objects.all().prefetch_related("children")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "parent"]
    search_fields    = ["name", "description"]
    ordering_fields  = ["name", "created_at"]
    lookup_field     = "slug"

    def get_queryset(self):
        qs = super().get_queryset()
        # By default, return only root categories unless ?parent= is set
        if "parent" not in self.request.query_params:
            qs = qs.filter(parent__isnull=True)
        if not self.request.user or not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        logger.info("Creating category: %s", serializer.validated_data.get("name"))
        serializer.save()

    def perform_update(self, serializer):
        logger.info("Updating category pk=%s", serializer.instance.pk)
        serializer.save()

    def perform_destroy(self, instance):
        logger.warning("Soft-deactivating category pk=%s", instance.pk)
        # Soft delete: deactivate instead of hard delete if it has children/products
        if instance.children.exists() or instance.products.exists():
            instance.is_active = False
            instance.save(update_fields=["is_active"])
        else:
            instance.delete()


# ──────────────────────────────────────────────────────────────────────────────
# Product ViewSet (Polymorphic)
# ──────────────────────────────────────────────────────────────────────────────

class ProductViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Products using polymorphic routing.
    product_type query param: book | electronics | fashion | generic
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "stock_status", "currency"]
    search_fields    = ["name", "sku", "description"]
    ordering_fields  = ["price", "created_at", "quantity", "name"]
    ordering         = ["-created_at"]

    PRODUCT_TYPE_MAP = {
        "book":        (Book,               BookSerializer),
        "electronics": (ElectronicsProduct, ElectronicsSerializer),
        "fashion":     (FashionProduct,     FashionSerializer),
    }

    def _get_type_info(self):
        ptype = self.request.query_params.get("product_type") or \
                self.request.data.get("product_type", "generic")
        return self.PRODUCT_TYPE_MAP.get(ptype, (Product, PolymorphicProductSerializer))

    def get_queryset(self):
        model_class, _ = self._get_type_info()
        qs = model_class.objects.select_related("category").prefetch_related("images", "variants")

        # Non-staff only see active products
        if not self.request.user or not self.request.user.is_staff:
            qs = qs.filter(status="active")

        # category filter (can be UUID or slug)
        category_param = self.request.query_params.get("category")
        if category_param:
            import uuid
            try:
                # Check if it's a valid UUID
                uuid.UUID(category_param)
                qs = qs.filter(category_id=category_param)
            except ValueError:
                # If it's a slug, filter by category slug or parent's slug
                qs = qs.filter(Q(category__slug=category_param) | Q(Q(category__parent__slug=category_param)))

        # price range filter
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        # seller filter (owner scope)
        seller_id = self.request.query_params.get("seller_id")
        if seller_id:
            qs = qs.filter(seller_id=seller_id)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        _, serializer_class = self._get_type_info()
        return serializer_class

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["product_type"] = self.request.query_params.get(
            "product_type",
            self.request.data.get("product_type", "generic")
        )
        return ctx

    @transaction.atomic
    def perform_create(self, serializer):
        """Inject seller_id from JWT token (inter-service auth)."""
        seller_id = None
        if self.request.user and self.request.user.is_authenticated:
            seller_id = self.request.user.id
        logger.info("Creating product type=%s seller=%s", self.request.data.get("product_type"), seller_id)
        serializer.save(seller_id=seller_id)

    @transaction.atomic
    def perform_update(self, serializer):
        logger.info("Updating product pk=%s", serializer.instance.pk)
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):
        """Hard delete product from database."""
        logger.warning("Hard-deleting product pk=%s sku=%s", instance.pk, instance.sku)
        instance.delete()

    # ── Domain Action Endpoints ───────────────────────────────────────────────

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="publish")
    def publish(self, request, pk=None):
        """Publish a draft product (domain action)."""
        product = self.get_object()
        try:
            product.publish()
            logger.info("Product pk=%s published by user=%s", product.pk, request.user.id)
            return Response({"detail": "Product published successfully."}, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="reserve-stock")
    def reserve_stock(self, request, pk=None):
        """Reserve stock for an order (called by order-service)."""
        product = self.get_object()
        qty = request.data.get("quantity")
        if not qty:
            return Response({"detail": "quantity is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product.reserve_stock(int(qty))
            logger.info("Stock reserved: product=%s qty=%s", product.pk, qty)
            return Response({
                "detail":       "Stock reserved.",
                "quantity":     product.quantity,
                "stock_status": product.stock_status,
            }, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="release-stock")
    def release_stock(self, request, pk=None):
        """Release reserved stock when an order is cancelled."""
        product = self.get_object()
        qty = request.data.get("quantity")
        if not qty:
            return Response({"detail": "quantity is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product.release_stock(int(qty))
            logger.info("Stock released: product=%s qty=%s", product.pk, qty)
            return Response({
                "detail":       "Stock released.",
                "quantity":     product.quantity,
                "stock_status": product.stock_status,
            }, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], permission_classes=[AllowAny], url_path="availability")
    def availability(self, request, pk=None):
        """Check if a product is available for purchase."""
        product = self.get_object()
        return Response({
            "product_id":   str(product.pk),
            "sku":          product.sku,
            "is_available": product.is_available(),
            "quantity":     product.quantity,
            "stock_status": product.stock_status,
        })

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="upload-image")
    def upload_image(self, request):
        """Upload an image file and return its URL."""
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        import uuid

        image_file = request.FILES.get("image") or request.FILES.get("file")
        if not image_file:
            return Response({"detail": "No image file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type
        ext = os.path.splitext(image_file.name)[1].lower() if hasattr(image_file, "name") else ".jpg"
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            return Response({"detail": "Invalid file type. Only JPG, PNG, WEBP, and GIF are allowed."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate unique name
        filename = f"products/{uuid.uuid4()}{ext}"
        
        # Save file
        path = default_storage.save(filename, ContentFile(image_file.read()))
        
        # Build URL
        from django.conf import settings
        url = f"{settings.MEDIA_URL}{path}"
        
        return Response({"url": url}, status=status.HTTP_201_CREATED)


# ──────────────────────────────────────────────────────────────────────────────
# Book ViewSet (dedicated endpoint for book-specific queries)
# ──────────────────────────────────────────────────────────────────────────────

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related("category").prefetch_related("images", "variants")
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["language", "genre", "status", "stock_status"]
    search_fields    = ["name", "sku", "author", "isbn", "publisher"]
    ordering_fields  = ["price", "published_at", "created_at"]

    @transaction.atomic
    def perform_create(self, serializer):
        seller_id = self.request.user.id if self.request.user.is_authenticated else None
        serializer.save(seller_id=seller_id)


# ──────────────────────────────────────────────────────────────────────────────
# Electronics ViewSet
# ──────────────────────────────────────────────────────────────────────────────

class ElectronicsViewSet(viewsets.ModelViewSet):
    queryset = ElectronicsProduct.objects.select_related("category").prefetch_related("images", "variants")
    serializer_class = ElectronicsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["brand", "os", "status", "stock_status"]
    search_fields    = ["name", "sku", "brand", "model_number"]
    ordering_fields  = ["price", "warranty_months", "created_at"]

    @transaction.atomic
    def perform_create(self, serializer):
        seller_id = self.request.user.id if self.request.user.is_authenticated else None
        serializer.save(seller_id=seller_id)


# ──────────────────────────────────────────────────────────────────────────────
# Fashion ViewSet
# ──────────────────────────────────────────────────────────────────────────────

class FashionViewSet(viewsets.ModelViewSet):
    queryset = FashionProduct.objects.select_related("category").prefetch_related("images", "variants")
    serializer_class = FashionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["brand", "gender", "season", "status", "stock_status"]
    search_fields    = ["name", "sku", "brand", "material"]
    ordering_fields  = ["price", "created_at"]

    @transaction.atomic
    def perform_create(self, serializer):
        seller_id = self.request.user.id if self.request.user.is_authenticated else None
        serializer.save(seller_id=seller_id)


# ──────────────────────────────────────────────────────────────────────────────
# ProductVariant & ProductImage ViewSets
# ──────────────────────────────────────────────────────────────────────────────

class ProductVariantViewSet(viewsets.ModelViewSet):
    """Manage variants for a given product (nested route)."""
    serializer_class   = ProductVariantSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return ProductVariant.objects.filter(product_id=self.kwargs["product_pk"])

    def perform_create(self, serializer):
        product = Product.objects.get(pk=self.kwargs["product_pk"])
        serializer.save(product=product)


class ProductImageViewSet(viewsets.ModelViewSet):
    """Manage images for a given product (nested route)."""
    serializer_class   = ProductImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return ProductImage.objects.filter(product_id=self.kwargs["product_pk"])

    def perform_create(self, serializer):
        product = Product.objects.get(pk=self.kwargs["product_pk"])
        serializer.save(product=product)
