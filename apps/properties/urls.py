from rest_framework.routers import DefaultRouter

from apps.properties.views import (
    PropertyViewSet,
    PropertySpecsViewSet,
    PropertyMediaViewSet,
    PropertyDocumentViewSet,
    PropertyFinancialInfoViewSet,
)

router = DefaultRouter()
router.register(r"properties", PropertyViewSet, basename="properties")
router.register(r"property-specs", PropertySpecsViewSet, basename="property-specs")
router.register(r"property-media", PropertyMediaViewSet, basename="property-media")
router.register(r"property-documents", PropertyDocumentViewSet, basename="property-documents")
router.register(r"property-financial-info", PropertyFinancialInfoViewSet, basename="property-financial-info")

urlpatterns = router.urls
