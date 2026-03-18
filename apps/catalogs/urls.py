from rest_framework.routers import DefaultRouter

from apps.catalogs.views import (
    PropertyTypeViewSet,
    PropertySubtypeViewSet,
    PropertyStatusViewSet,
    PropertyConditionViewSet,
    OperationTypeViewSet,
    PaymentMethodViewSet,
    CurrencyViewSet,
    DocumentTypeViewSet,
    UtilityServiceViewSet,
    CanalLeadViewSet,
    LeadStatusViewSet,
    EventTypeViewSet,
)

router = DefaultRouter()
router.register(r"property-types", PropertyTypeViewSet, basename="property-types")
router.register(r"property-subtypes", PropertySubtypeViewSet, basename="property-subtypes")
router.register(r"property-statuses", PropertyStatusViewSet, basename="property-statuses")
router.register(r"property-conditions", PropertyConditionViewSet, basename="property-conditions")
router.register(r"operation-types", OperationTypeViewSet, basename="operation-types")
router.register(r"payment-methods", PaymentMethodViewSet, basename="payment-methods")
router.register(r"currencies", CurrencyViewSet, basename="currencies")
router.register(r"document-types", DocumentTypeViewSet, basename="document-types")
router.register(r"utility-services", UtilityServiceViewSet, basename="utility-services")
router.register(r"canal-leads", CanalLeadViewSet, basename="canal-leads")
router.register(r"lead-statuses", LeadStatusViewSet, basename="lead-statuses")
router.register(r"event-types", EventTypeViewSet, basename="event-types")

urlpatterns = router.urls
