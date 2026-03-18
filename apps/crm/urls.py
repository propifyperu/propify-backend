from rest_framework.routers import DefaultRouter

from apps.crm.views import (
    ContactViewSet,
    LeadViewSet,
    RequirementViewSet,
    RequirementMatchViewSet,
    MatchViewSet,
    EventViewSet,
)

router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contacts")
router.register(r"leads", LeadViewSet, basename="leads")
router.register(r"requirements", RequirementViewSet, basename="requirements")
router.register(r"requirement-matches", RequirementMatchViewSet, basename="requirement-matches")
router.register(r"matches", MatchViewSet, basename="matches")
router.register(r"events", EventViewSet, basename="events")

urlpatterns = router.urls
