"""core/urls.py – Root URL configuration for product-service."""
from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "service": "product-service"})


urlpatterns = [
    path("admin/",        admin.site.urls),
    path("api/health/",   health_check, name="health-check"),
    path("api/schema/",   SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",     SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("",              include("apps.products.presentation.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
