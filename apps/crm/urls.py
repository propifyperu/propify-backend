from rest_framework.routers import DefaultRouter

from apps.crm.views import (
    ContactViewSet,
    DashboardViewSet,
    EventViewSet,
    LeadViewSet,
    MatchViewSet,
    RequirementMatchViewSet,
    RequirementViewSet,
)

router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contacts")
router.register(r"leads", LeadViewSet, basename="leads")
router.register(r"requirements", RequirementViewSet, basename="requirements")
router.register(r"requirement-matches", RequirementMatchViewSet, basename="requirement-matches")
router.register(r"matches", MatchViewSet, basename="matches")
router.register(r"events", EventViewSet, basename="events")
router.register(r"dashboard", DashboardViewSet, basename="dashboard")

urlpatterns = router.urls
