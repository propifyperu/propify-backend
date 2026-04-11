from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.views import AreaViewSet, RoleViewSet, UserProfileViewSet, UserViewSet
from apps.users.views.auth import GoogleLoginView

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("profiles", UserProfileViewSet, basename="profiles")
router.register("areas", AreaViewSet, basename="areas")
router.register("roles", RoleViewSet, basename="roles")

urlpatterns = [
    path("auth/google/", GoogleLoginView.as_view(), name="google-login"),
    path("", include(router.urls)),
]