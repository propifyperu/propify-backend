from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.locations.views import (
    CountryViewSet,
    DepartmentViewSet,
    DistrictViewSet,
    ProvinceViewSet,
    UrbanizationViewSet,
)

router = DefaultRouter()
router.register("countries", CountryViewSet, basename="countries")
router.register("departments", DepartmentViewSet, basename="departments")
router.register("provinces", ProvinceViewSet, basename="provinces")
router.register("districts", DistrictViewSet, basename="districts")
router.register("urbanizations", UrbanizationViewSet, basename="urbanizations")

urlpatterns = [
    path("", include(router.urls)),
]
